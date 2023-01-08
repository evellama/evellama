import csv
import concurrent.futures
import multiprocessing as mp
import io
import pandas as pd
import numpy as np
import time
from evellama.data import DATA_BUCKET_RAW, DATA_BUCKET_STAGE, s3
from evellama.logging import critical, debug, error, info, warning
from evellama.market import MARKET_EXCHANGES, MARKET_REGION_DEPTH_SNAPSHOT_REGION_IDS
from sqlalchemy import create_engine
from airflow.models import Variable


def transform_and_load_exchange_depths(extracted_orders):
    if not extracted_orders:
        info("No orders to aggregate depths from")
        return

    orders_df = s3.read_parquet(list(extracted_orders.values()))[
        [
            "order_id",
            "region_id",
            "location_id",
            "type_id",
            "is_buy_order",
            "price",
            "volume_remain",
        ]
    ]

    depths_df = (
        orders_df.groupby(
            ["region_id", "location_id", "type_id", "is_buy_order", "price"]
        )
        .agg(count=("order_id", "count"), volume=("volume_remain", np.sum))
        .reset_index()
    )
    depths_df["value"] = depths_df["price"] * depths_df["volume"]
    depths_paths = {}
    for region_id, region_df in depths_df.groupby("region_id"):
        if region_id in MARKET_EXCHANGES:
            orders_path = next(
                k
                for k in list(extracted_orders.values())
                if k.startswith(
                    f"s3://{DATA_BUCKET_RAW}/market_region_orders/{region_id}"
                )
            )

            for exchange_name, exchange_locations in MARKET_EXCHANGES[
                region_id
            ].items():
                depths_path = (
                    orders_path.replace(
                        "market_region_orders", "market_exchange_depths"
                    )
                    .replace(DATA_BUCKET_RAW, DATA_BUCKET_STAGE)
                    .replace(str(region_id), exchange_name)
                )

                exchange_depths_df = region_df[
                    (region_df["region_id"] == region_id)
                    & (region_df["location_id"].isin(exchange_locations))
                ]

                if s3.does_object_exist(depths_path):
                    warning(
                        f"Market exchange depths already exist at {depths_path} for {orders_path}"
                    )

                s3.to_parquet(exchange_depths_df, depths_path)
                depths_paths[exchange_name] = depths_path
                info(
                    f"Wrote {len(exchange_depths_df.index)} depths(s) for exchange {exchange_name} from {len(orders_df[orders_df['region_id']==region_id].index)} order(s) in region {region_id} to {depths_path}"
                )
    info(f"Wrote depths for {len(depths_paths)} exchange(s)")

    # load_market_exchange_depths_db(depths_paths)

    return depths_paths


# def load_market_exchange_depths_db(depths_paths):
#     engine = create_engine(Variable.get("EVELLAMA_DATABASE_URL"))
#     depths_df = s3.read_parquet(list(depths_paths.values()))[
#         [
#     "region_id"
#     "type_id"
#      "count"
#     "price"
#      "is_buy_order"
#     "last_modified"
#      "volume"
#         ]
#     ].rename(columns={ 'type_id': 'item_id' })

#     depths_df['timestamp'] =
#     depths_df['side'] = np.where(depths_df['is_buy_order'], 'buy', 'sell')

#     conn = engine.raw_connection()
#     cur = conn.cursor()
#     output = io.StringIO()
#     orders_df.to_csv(output, sep="\t", header=False, index=False)
#     output.seek(0)
#     output.getvalue()
#     cur.copy_expert("COPY market_orders FROM STDIN", output)
#     conn.commit()


def transform_and_load_region_depths(extracted_orders):
    if not extracted_orders:
        info("No orders to aggregate depths from")
        return

    orders_df = s3.read_parquet(list(extracted_orders.values()))[
        [
            "order_id",
            "region_id",
            "type_id",
            "is_buy_order",
            "price",
            "volume_remain",
            "last_modified",
        ]
    ]

    depths_df = (
        orders_df.groupby(
            ["last_modified", "region_id", "type_id", "is_buy_order", "price"]
        )
        .agg(
            count=("order_id", "count"),
            volume=("volume_remain", np.sum),
        )
        .reset_index()
    )
    depths_df["value"] = depths_df["price"] * depths_df["volume"]
    depths_paths = {}
    for region_id, region_df in depths_df.groupby("region_id"):
        last_modified = region_df["last_modified"].values[0]
        orders_path = next(
            k
            for k in list(extracted_orders.values())
            if k.startswith(f"s3://{DATA_BUCKET_RAW}/market_region_orders/{region_id}")
        )
        depths_path = orders_path.replace(
            "market_region_orders", "market_region_depths"
        ).replace(DATA_BUCKET_RAW, DATA_BUCKET_STAGE)

        if s3.does_object_exist(depths_path):
            warning(
                f"Market region depths already exist at {depths_path} for {orders_path}"
            )

        region_df["last_modified"] = last_modified

        s3.to_parquet(region_df, depths_path)
        depths_paths[int(region_id)] = depths_path
        info(
            f"Wrote {len(region_df.index)} depths(s) from {len(orders_df[orders_df['region_id']==region_id].index)} order(s) for region {region_id} to {depths_path}"
        )

    info(f"Wrote depths for {len(depths_paths)} region(s)")

    load_market_region_depths_db(depths_paths)

    return depths_paths


def load_market_region_depths_db(depths_paths):
    depths_df = s3.read_parquet(list(depths_paths.values()))[
        [
            "region_id",
            "type_id",
            "count",
            "price",
            "is_buy_order",
            "last_modified",
            "volume",
        ]
    ]

    depths_df = depths_df[
        depths_df["region_id"].isin(MARKET_REGION_DEPTH_SNAPSHOT_REGION_IDS)
    ]

    if depths_df.empty:
        info(f"No depth levels to transform")
        return

    start_time = time.perf_counter()
    types = []
    with concurrent.futures.ProcessPoolExecutor(
        mp_context=mp.get_context("fork")
    ) as exe:
        futures = {
            exe.submit(process_type_levels, group_idx, group_df): group_idx
            for group_idx, group_df in depths_df.groupby(
                ["last_modified", "region_id", "type_id"]
            )
        }
        for future in concurrent.futures.as_completed(futures):
            types.append(future.result())

    levels_df = pd.DataFrame.from_dict(types)
    levels_df["timestamp"] = pd.Series(levels_df["timestamp"]).dt.floor("5T")
    end_time = time.perf_counter()
    info(
        f"Transformed {len(levels_df)} depth snapshot(s) for {len(MARKET_REGION_DEPTH_SNAPSHOT_REGION_IDS)} region(s) in {end_time - start_time:0.4f} seconds"
    )

    database_url = Variable.get("EVELLAMA_DATABASE_URL", default_var=None)
    if not database_url:
        warning(f"EVELLAMA_DATABASE_URL is not configured. Depth snapshots will not be loaded into the database.")
        return

    start_time = time.perf_counter()
    engine = create_engine(Variable.get("EVELLAMA_DATABASE_URL"))
    conn = engine.raw_connection()
    cur = conn.cursor()
    output = io.StringIO()
    levels_df.to_csv(
        output, sep="\t", header=False, index=False, quoting=csv.QUOTE_NONE
    )
    output.seek(0)
    output.getvalue()
    cur.copy_expert("COPY market_region_depth_snapshots FROM STDIN", output)
    conn.commit()
    end_time = time.perf_counter()

    info(
        f"Loaded {len(levels_df)} depth snapshot(s) for {len(MARKET_REGION_DEPTH_SNAPSHOT_REGION_IDS)} region(s) in {end_time - start_time:0.4f} seconds"
    )


def process_type_levels(group_idx, group_df):
    last_modified, region_id, type_id = group_idx

    sell_levels = (
        group_df[~group_df["is_buy_order"]][["price", "count", "volume"]]
        .sort_values(by="price", ascending=False)
        .rename(columns={"price": "p", "count": "c", "volume": "v"})
    )

    buy_levels = (
        group_df[group_df["is_buy_order"]][["price", "count", "volume"]]
        .sort_values(by="price")
        .rename(columns={"price": "p", "count": "c", "volume": "v"})
    )

    return {
        "region_id": region_id,
        "type_id": type_id,
        "buy_levels": buy_levels.to_json(orient="records"),
        "sell_levels": sell_levels.to_json(orient="records"),
        "timestamp": last_modified,
    }

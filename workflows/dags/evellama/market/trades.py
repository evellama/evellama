import numpy as np
import pandas as pd
import pendulum
import re
from awswrangler.exceptions import EmptyDataFrame
from evellama.logging import critical, debug, error, info, warning
from evellama.data import DATA_BUCKET_RAW, DATA_BUCKET_STAGE, s3
from evellama.market import MARKET_EXCHANGES


def extract_region_trades(extracted_orders):
    if not extracted_orders:
        info("No orders to extract trades from")
        return {}

    trade_orders_paths = {}
    for region_id, current_path in extracted_orders.items():
        trade_orders_path = current_path.replace(
            "market_region_orders", "market_region_trade_orders"
        ).replace(DATA_BUCKET_RAW, DATA_BUCKET_STAGE)

        if s3.does_object_exist(trade_orders_path):
            warning(f"Market trades already exist at {trade_orders_path}")

        prefix = f"market_region_orders/{region_id}"

        current_filestamp = re.findall(r"(\d{4}/\d{2}/\d{2})", current_path)[0]
        current_timestamp = pendulum.from_format(
            current_filestamp, "YYYY/MM/DD", tz="UTC"
        )

        current_day_prefix = (
            f"s3://{DATA_BUCKET_RAW}/{prefix}/{current_timestamp.format('YYYY/MM/DD')}"
        )
        current_day_paths = s3.list_objects(current_day_prefix)

        previous_day_prefix = f"s3://{DATA_BUCKET_RAW}/{prefix}/{current_timestamp.subtract(days=1).format('YYYY/MM/DD')}"
        previous_day_paths = s3.list_objects(previous_day_prefix)

        paths = sorted(current_day_paths + previous_day_paths)
        current_index = paths.index(current_path)

        try:
            previous_path = paths[current_index - 1]
        except IndexError:
            warning("No previous orders for {current_path}")
            continue

        previous_filestamp = re.findall(r"(\d{4}/\d{2}/\d{2})", previous_path)[0]
        previous_timestamp = pendulum.from_format(
            previous_filestamp, "YYYY/MM/DD", tz="UTC"
        )

        previous_diff = previous_timestamp.diff(current_timestamp).in_minutes()
        if previous_diff > 6:
            warning(f"Previous orders greater than ~5min old: {previous_diff}")
            continue

        current_orders_df = s3.read_parquet(current_path)
        previous_orders_df = s3.read_parquet(previous_path)

        current_orders_df["volume_remain"] = -current_orders_df["volume_remain"]
        all_orders_df = pd.concat(
            [previous_orders_df, current_orders_df], ignore_index=True
        )

        trade_volumes_df = (
            all_orders_df.groupby(["order_id"])
            .agg(
                count=("order_id", "count"),
                volume_traded=("volume_remain", lambda x: np.abs(np.sum(x))),
            )
            .reset_index()
        )
        trade_volumes_df = trade_volumes_df[
            (trade_volumes_df["volume_traded"].gt(0)) & (trade_volumes_df["count"] == 2)
        ].set_index(["order_id"])

        if trade_volumes_df.empty:
            info(
                f"No trades from {len(current_orders_df.index)} order(s) in region {region_id} from {current_path}"
            )
            continue

        current_orders_df = current_orders_df.set_index(["order_id"])
        trade_orders_df = current_orders_df.join(trade_volumes_df, how="inner")
        trade_orders_df["volume_remain"] = -trade_orders_df["volume_remain"]
        trade_orders_df["value_traded"] = (
            trade_orders_df["price"] * trade_orders_df["volume_traded"]
        )
        trade_orders_df = trade_orders_df.drop(columns=["count"]).reset_index()

        s3.to_parquet(trade_orders_df, trade_orders_path)
        trade_orders_paths[region_id] = trade_orders_path
        info(
            f"Wrote {len(trade_orders_df.index)} trade order(s) from {len(current_orders_df.index)} order(s) in region {region_id} to {trade_orders_path}"
        )

    info(f"Wrote trade orders for {len(trade_orders_paths)} region(s)")

    return trade_orders_paths


def load_region_trades_db(extracted_trades):
    return extracted_trades


def transform_and_load_exchange_trade_flows(extracted_trade_orders):
    if not extracted_trade_orders:
        info("No trade orders to aggregate trade flows from")
        return

    trade_orders_df = s3.read_parquet(list(extracted_trade_orders.values()))
    last_modified = trade_orders_df["last_modified"].values[0]

    trade_flows_paths = {}
    for region_id, region_df in trade_orders_df.groupby(["region_id"]):
        if region_id in MARKET_EXCHANGES:
            trade_orders_path = next(
                k
                for k in list(extracted_trade_orders.values())
                if k.startswith(
                    f"s3://{DATA_BUCKET_STAGE}/market_region_trade_orders/{region_id}"
                )
            )

            for exchange_name, exchange_locations in MARKET_EXCHANGES[
                region_id
            ].items():
                trade_flows_path = trade_orders_path.replace(
                    "market_region_trade_orders", "market_exchange_trade_flows"
                ).replace(str(region_id), exchange_name)

                exchange_orders_df = region_df[
                    (region_df["region_id"] == region_id)
                    & (region_df["location_id"].isin(exchange_locations))
                ]

                trade_flows_df = (
                    exchange_orders_df.groupby(["type_id", "is_buy_order", "price"])
                    .agg(
                        count=("order_id", "count"),
                        volume=("volume_traded", np.sum),
                        value=("value_traded", np.sum),
                    )
                    .reset_index()
                )

                trade_flows_df["last_modified"] = last_modified

                if trade_flows_df.empty:
                    warning("Trade flows data frame is empty!")
                    continue

                s3.to_parquet(trade_flows_df, trade_flows_path)
                trade_flows_paths[exchange_name] = trade_flows_path
                info(
                    f"Wrote {len(trade_flows_df.index)} trade flow(s) from {len(exchange_orders_df.index)} order(s) for exchange {exchange_name} in region {region_id} to {trade_flows_path}"
                )

    info(f"Wrote trade flows for {len(trade_flows_paths)} exchange(s)")

    return trade_flows_paths


def transform_and_load_region_trade_flows(extracted_trade_orders):
    if not extracted_trade_orders:
        info("No trade orders to aggregate trade flows from")
        return {}

    trade_orders_df = s3.read_parquet(list(extracted_trade_orders.values()))
    last_modified = trade_orders_df["last_modified"].values[0]

    trade_flows_paths = {}
    for region_id, region_df in trade_orders_df.groupby(["region_id"]):
        trade_orders_path = next(
            k
            for k in list(extracted_trade_orders.values())
            if k.startswith(
                f"s3://{DATA_BUCKET_STAGE}/market_region_trade_orders/{region_id}"
            )
        )
        trade_flows_path = trade_orders_path.replace(
            "market_region_trade_orders", "market_region_trade_flows"
        )

        trade_flows_df = (
            region_df.groupby(["type_id", "is_buy_order", "price"])
            .agg(
                count=("order_id", "count"),
                volume=("volume_traded", np.sum),
                value=("value_traded", np.sum),
            )
            .reset_index()
        )

        trade_flows_df["last_modified"] = last_modified

        s3.to_parquet(trade_flows_df, trade_flows_path)
        trade_flows_paths[int(region_id)] = trade_flows_path
        info(
            f"Wrote {len(trade_flows_df.index)} trade flow(s) from {len(trade_orders_df.index)} trade order(s) in region {region_id} to {trade_flows_path}"
        )

    info(f"Wrote trade flows for {len(trade_flows_paths)} region(s)")

    return trade_flows_paths

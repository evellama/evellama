from itertools import groupby
import pandas as pd
import numpy as np
from evellama.data import DATA_BUCKET_RAW, DATA_BUCKET_STAGE, s3
from evellama.logging import critical, debug, error, info, warning
from evellama.market import MARKET_EXCHANGES


def transform_and_load_exchange_quotes(extracted_orders):
    if not extracted_orders:
        info("No orders to aggregate quotes from")
        return

    orders_df = s3.read_parquet(list(extracted_orders.values()))[
        [
            "order_id",
            "region_id",
            "system_id",
            "location_id",
            "type_id",
            "is_buy_order",
            "price",
            "volume_remain",
            "duration",
            "range",
            "issued",
            "last_modified",
            "min_volume",
        ]
    ]

    quotes_paths = {}
    for region_id, region_df in orders_df.groupby("region_id"):
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
                quotes_path = (
                    orders_path.replace(
                        "market_region_orders", "market_exchange_quotes"
                    )
                    .replace(DATA_BUCKET_RAW, DATA_BUCKET_STAGE)
                    .replace(str(region_id), exchange_name)
                )

                exchange_orders_df = region_df[
                    (region_df["region_id"] == region_id)
                    & (region_df["location_id"].isin(exchange_locations))
                ]
                exchange_df = transform_and_load_quotes(
                    exchange_orders_df, groupby=["type_id"]
                )
                exchange_df = join_quotes(exchange_df)

                if s3.does_object_exist(quotes_path):
                    warning(
                        f"Market exchange quotes already exist at {quotes_path} for {orders_path}"
                    )

                s3.to_parquet(exchange_df, quotes_path)
                quotes_paths[exchange_name] = quotes_path
                info(
                    f"Wrote {len(exchange_df.index)} quotes(s) from {len(exchange_orders_df.index)} order(s) for exchange {exchange_name} in region {region_id} to {quotes_path}"
                )
    info(f"Wrote quotes for {len(quotes_paths)} exchange(s)")
    return quotes_paths


def transform_and_load_region_quotes(extracted_orders):
    if not extracted_orders:
        info("No orders to aggregate quotes from")
        return

    orders_df = s3.read_parquet(list(extracted_orders.values()))[
        [
            "order_id",
            "region_id",
            "system_id",
            "location_id",
            "type_id",
            "is_buy_order",
            "price",
            "volume_remain",
            "duration",
            "range",
            "issued",
            "last_modified",
            "min_volume",
        ]
    ]

    quotes_df = transform_and_load_quotes(orders_df)
    quotes_paths = {}
    for region_id, region_df in quotes_df.groupby("region_id"):
        orders_path = next(
            k
            for k in list(extracted_orders.values())
            if k.startswith(f"s3://{DATA_BUCKET_RAW}/market_region_orders/{region_id}")
        )
        quotes_path = orders_path.replace(
            "market_region_orders", "market_region_quotes"
        ).replace(DATA_BUCKET_RAW, DATA_BUCKET_STAGE)

        region_df = join_quotes(region_df)

        if s3.does_object_exist(quotes_path):
            warning(
                f"Market region quotes already exist at {quotes_path} for {orders_path}"
            )

        s3.to_parquet(region_df, quotes_path)
        quotes_paths[int(region_id)] = quotes_path
        info(
            f"Wrote {len(region_df.index)} quotes(s) from {len(orders_df[orders_df['region_id']==region_id].index)} order(s) for region {region_id} to {quotes_path}"
        )
    info(f"Wrote quotes for {len(quotes_paths)} region(s)")
    return quotes_paths


def transform_and_load_quotes(orders_df, groupby=["region_id", "type_id"]):
    buy_orders_df = orders_df[orders_df["is_buy_order"]].reset_index()
    buy_orders_df = buy_orders_df.loc[
        buy_orders_df.reset_index().groupby(groupby)["price"].idxmax()
    ]
    sell_orders_df = orders_df[~orders_df["is_buy_order"]].reset_index()
    sell_orders_df = sell_orders_df.loc[
        sell_orders_df.reset_index().groupby(groupby)["price"].idxmin()
    ]
    quotes_df = pd.concat([buy_orders_df, sell_orders_df])
    return quotes_df.rename(columns={"volume_remain": "volume"})


def join_quotes(quotes_df):
    buy_orders_df = (
        quotes_df[quotes_df["is_buy_order"]]
        .drop(columns=["is_buy_order"])
        .add_prefix("buy_")
        .rename(
            columns={
                "buy_region_id": "region_id",
                "buy_type_id": "type_id",
                "buy_last_modified": "last_modified",
            }
        )
        .set_index(["region_id", "type_id", "last_modified"])
    )
    sell_orders_df = (
        quotes_df[~quotes_df["is_buy_order"]]
        .drop(columns=["is_buy_order"])
        .add_prefix("sell_")
        .rename(
            columns={
                "sell_region_id": "region_id",
                "sell_type_id": "type_id",
                "sell_last_modified": "last_modified",
            }
        )
        .set_index(["region_id", "type_id", "last_modified"])
    )

    joined_df = (
        buy_orders_df.join(sell_orders_df, how="outer")
        .drop(columns=["buy_index", "sell_index"])
        .reset_index()
    )
    return joined_df


def key_func(k):
    return (k["region_id"], k["type_id"])


def aggregate_all_region_quotes(paths):
    results = {}
    for region_id, path in paths.items():
        results[region_id] = aggregate_region_quotes(region_id, path)
    return results


def aggregate_region_quotes(region_id, latest):
    path = latest.replace("market_region_orders", "market_region_quotes").replace(
        DATA_BUCKET_RAW, DATA_BUCKET_STAGE
    )

    if s3.does_object_exist(path):
        warning(f"Market order quotes already exist at {path} for {latest}")
        return False

    orders_df = s3.read_parquet(latest)
    orders_df = concat_with_outliers_and_five_pct(orders_df)

    agg_prices_df = aggregate_quotes(orders_df)
    agg_five_pct_df = aggregate_five_pct_prices(orders_df)
    prices_df = agg_prices_df.join(agg_five_pct_df, how="outer")

    s3.to_parquet(prices_df, path)
    info(
        f"Wrote {len(prices_df.index)} price(s) from {len(orders_df.index)} order(s)for region {region_id} to {path}"
    )

    return path


def aggregate_quotes(orders_df, prefix=None):
    orders_df = orders_df[~orders_df["outlier"]]
    orders_df["value"] = orders_df["volume_remain"] * orders_df["price"]

    results = orders_df.groupby(["type_id", "is_buy_order"]).agg(
        count=("order_id", "count"),
        outlier_count=("outlier", "count"),
        outlier_threshold=("outlier", np.max),
        price_min=("price", np.min),
        price_max=("price", np.max),
        price_avg=("price", np.mean),
        price_std=("price", np.std),
        price_var=("price", np.var),
        price_med=("price", np.median),
        value_sum=("value", np.sum),
        value_min=("value", np.min),
        value_max=("value", np.max),
        value_avg=("value", np.mean),
        value_std=("value", np.std),
        value_var=("value", np.var),
        value_med=("value", np.median),
        volume_sum=("volume_remain", np.sum),
        volume_min=("volume_remain", np.min),
        volume_max=("volume_remain", np.max),
        volume_avg=("volume_remain", np.mean),
        volume_std=("volume_remain", np.std),
        volume_var=("volume_remain", np.var),
        volume_med=("volume_remain", np.median),
    )
    results = results.reset_index().set_index(["type_id", "is_buy_order"])

    return results


def aggregate_five_pct_prices(orders_df):
    orders_df = orders_df[orders_df["five_pct"]]
    orders_df["value"] = orders_df["volume_remain"] * orders_df["price"]
    results = orders_df.groupby(["type_id", "is_buy_order"]).agg(
        five_pct_count=("order_id", "count"),
        five_pct_price_min=("price", np.min),
        five_pct_price_max=("price", np.max),
        five_pct_price_avg=("price", np.mean),
        five_pct_price_std=("price", np.std),
        five_pct_price_var=("price", np.var),
        five_pct_price_med=("price", np.median),
        five_pct_value_sum=("value", np.sum),
        five_pct_value_min=("value", np.min),
        five_pct_value_max=("value", np.max),
        five_pct_value_avg=("value", np.mean),
        five_pct_value_std=("value", np.std),
        five_pct_value_var=("value", np.var),
        five_pct_value_med=("value", np.median),
        five_pct_volume_sum=("volume_remain", np.sum),
        five_pct_volume_min=("volume_remain", np.min),
        five_pct_volume_max=("volume_remain", np.max),
        five_pct_volume_avg=("volume_remain", np.mean),
        five_pct_volume_std=("volume_remain", np.std),
        five_pct_volume_var=("volume_remain", np.var),
        five_pct_volume_med=("volume_remain", np.median),
    )
    results = results.reset_index().set_index(["type_id", "is_buy_order"])
    return results


def concat_with_outliers_and_five_pct(orders_df):
    dfs = list()
    dfs.append(mark_buy_outliers_and_five_pct(orders_df))
    dfs.append(mark_sell_outliers_and_five_pct(orders_df))

    concat_df = pd.concat(
        list(filter(lambda df: df is not None, dfs)),
        ignore_index=True,
    )
    return concat_df


def mark_buy_outliers_and_five_pct(orders_df):
    buy_orders_df = orders_df[orders_df["is_buy_order"]][
        ["order_id", "region_id", "type_id", "price", "volume_remain"]
    ]
    buy_orders_dict = buy_orders_df.to_dict("records")

    if not buy_orders_dict:
        print("No buy orders")
        return

    for _key, value in groupby(sorted(buy_orders_dict, key=key_func), key_func):
        group_orders = list(value)
        prices = [o["price"] for o in group_orders]

        # Outliers are orders that have a price less than 10% of the maximum buy order
        lower_limit = np.max(prices) * 0.1
        for o in group_orders:
            o["outlier_threshold"] = lower_limit
            if not o["price"] <= lower_limit:
                o["outlier"] = False
            else:
                o["outlier"] = True

        five_pct_quantile = np.quantile(
            [o["volume_remain"] for o in group_orders if not o["outlier"]], 0.95
        )
        for o in group_orders:
            if o["outlier"]:
                o["five_pct"] = False
                continue

            o["five_pct_threshold"] = five_pct_quantile
            if o["volume_remain"] >= five_pct_quantile:
                o["five_pct"] = True
            else:
                o["five_pct"] = False

    buy_orders_df = pd.DataFrame.from_dict(buy_orders_dict)
    buy_orders_df["is_buy_order"] = True

    return buy_orders_df


def mark_sell_outliers_and_five_pct(orders_df):
    sell_orders_df = orders_df[~orders_df["is_buy_order"]][
        ["order_id", "region_id", "type_id", "price", "volume_remain"]
    ]
    sell_orders_dict = sell_orders_df.to_dict("records")

    if not sell_orders_dict:
        print("No sell orders")
        return

    for key, value in groupby(sorted(sell_orders_dict, key=key_func), key_func):
        group_orders = list(value)
        prices = [o["price"] for o in group_orders]

        # Outliers are orders that have a price greater than 10 times the minimum sell order
        upper_limit = np.min(prices) * 10.0
        for o in group_orders:
            o["outlier_threshold"] = upper_limit
            if not o["price"] >= upper_limit:
                o["outlier"] = False
            else:
                o["outlier"] = True

        five_pct_quantile = np.quantile(
            [o["volume_remain"] for o in group_orders if not o["outlier"]], 0.95
        )
        for o in group_orders:
            if o["outlier"]:
                o["five_pct"] = False
                continue

            o["five_pct_threshold"] = five_pct_quantile
            if o["volume_remain"] >= five_pct_quantile:
                o["five_pct"] = True
            else:
                o["five_pct"] = False

    sell_orders_df = pd.DataFrame.from_dict(sell_orders_dict)
    sell_orders_df["is_buy_order"] = False

    return sell_orders_df

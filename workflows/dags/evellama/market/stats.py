from itertools import groupby
import pandas as pd
import numpy as np
from evellama.data import DATA_BUCKET_RAW, DATA_BUCKET_STAGE, s3
from evellama.logging import critical, debug, error, info, warning
from evellama.market import MARKET_EXCHANGES


def transform_and_load_exchange_stats(extracted_orders, extracted_trade_orders):
    if not extracted_orders:
        info("No orders to aggregate stats from")
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
            "last_modified",
        ]
    ]

    if extracted_trade_orders:
        trade_orders_df = s3.read_parquet(list(extracted_trade_orders.values()))
    else:
        trade_orders_df = None

    stats_paths = {}
    for region_id, region_df in orders_df.groupby(["region_id"]):
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
                stats_path = (
                    orders_path.replace("market_region_orders", "market_exchange_stats")
                    .replace(DATA_BUCKET_RAW, DATA_BUCKET_STAGE)
                    .replace(str(region_id), exchange_name)
                )

                exchange_orders_df = region_df[
                    (region_df["region_id"] == region_id)
                    & (region_df["location_id"].isin(exchange_locations))
                ]

                if trade_orders_df is not None:
                    exchange_trade_orders_df = trade_orders_df[
                        (trade_orders_df["region_id"] == region_id)
                        & (trade_orders_df["location_id"].isin(exchange_locations))
                    ]
                else:
                    exchange_trade_orders_df = None

                exchange_df = aggregate_stats(
                    exchange_orders_df, exchange_trade_orders_df
                )

                if s3.does_object_exist(stats_path):
                    warning(
                        f"Market exchange stats already exist at {stats_path} for {orders_path}"
                    )

                s3.to_parquet(exchange_df, stats_path)
                stats_paths[exchange_name] = stats_path
                info(
                    f"Wrote {len(exchange_df.index)} stats(s) from {len(exchange_orders_df.index)} order(s) for exchange {exchange_name} in region {region_id} to {stats_path}"
                )
    info(f"Wrote stats for {len(stats_paths)} exchange(s)")
    return stats_paths


def transform_and_load_region_stats(extracted_orders, extracted_trade_orders):
    if not extracted_orders:
        info("No orders to aggregate stats from")
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

    if extracted_trade_orders:
        trade_orders_df = s3.read_parquet(list(extracted_trade_orders.values()))
    else:
        trade_orders_df = None

    stats_df = aggregate_stats(orders_df, trade_orders_df)
    stats_paths = {}
    for region_id, region_df in stats_df.groupby(["region_id"]):
        orders_path = next(
            k
            for k in list(extracted_orders.values())
            if k.startswith(f"s3://{DATA_BUCKET_RAW}/market_region_orders/{region_id}")
        )
        stats_path = orders_path.replace(
            "market_region_orders", "market_region_stats"
        ).replace(DATA_BUCKET_RAW, DATA_BUCKET_STAGE)

        if s3.does_object_exist(stats_path):
            warning(
                f"Market region stats already exist at {stats_path} for {orders_path}"
            )

        s3.to_parquet(region_df, stats_path)
        stats_paths[region_id] = stats_path
        info(
            f"Wrote {len(region_df.index)} stats(s) from {len(orders_df[orders_df['region_id']==region_id].index)} order(s) for region {region_id} to {stats_path}"
        )
    info(f"Wrote stats for {len(stats_paths)} region(s)")
    return stats_paths


def key_func(k):
    return (k["region_id"], k["type_id"])


def aggregate_stats(orders_df, trade_orders_df=None):
    orders_df = concat_with_outliers_and_five_pct(orders_df)

    agg_prices_df = aggregate_order_stats(orders_df)
    agg_five_pct_df = aggregate_five_pct_order_stats(orders_df)
    stats_df = agg_prices_df.join(agg_five_pct_df, how="outer").reset_index()

    buy_stats_df = (
        stats_df[stats_df["is_buy_order"]]
        .drop(columns=["is_buy_order"])
        .add_prefix("buy_order_")
        .rename(
            columns={
                "buy_order_region_id": "region_id",
                "buy_order_type_id": "type_id",
                "buy_order_last_modified": "last_modified",
            }
        )
        .set_index(["region_id", "type_id", "last_modified"])
    )
    sell_stats_df = (
        stats_df[~stats_df["is_buy_order"]]
        .drop(columns=["is_buy_order"])
        .add_prefix("sell_order_")
        .rename(
            columns={
                "sell_order_region_id": "region_id",
                "sell_order_type_id": "type_id",
                "sell_order_last_modified": "last_modified",
            }
        )
        .set_index(["region_id", "type_id", "last_modified"])
    )

    joined_df = buy_stats_df.join(sell_stats_df, how="outer")

    if trade_orders_df is not None:
        trade_stats_df = aggregate_trade_stats(trade_orders_df).reset_index()
        trade_buy_stats_df = (
            trade_stats_df[trade_stats_df["is_buy_order"]]
            .drop(columns=["is_buy_order"])
            .add_prefix("buy_trade_")
            .rename(
                columns={
                    "buy_trade_region_id": "region_id",
                    "buy_trade_type_id": "type_id",
                    "buy_trade_last_modified": "last_modified",
                }
            )
            .set_index(["region_id", "type_id", "last_modified"])
        )
        trade_sell_stats_df = (
            trade_stats_df[~trade_stats_df["is_buy_order"]]
            .drop(columns=["is_buy_order"])
            .add_prefix("sell_trade_")
            .rename(
                columns={
                    "sell_trade_region_id": "region_id",
                    "sell_trade_type_id": "type_id",
                    "sell_trade_last_modified": "last_modified",
                }
            )
            .set_index(["region_id", "type_id", "last_modified"])
        )
        trade_stats_df = trade_buy_stats_df.join(trade_sell_stats_df, how="outer")
        joined_df = joined_df.join(trade_stats_df, how="outer")

    return joined_df.reset_index()


def concat_with_outliers_and_five_pct(orders_df):
    dfs = list()
    dfs.append(mark_buy_outliers_and_five_pct(orders_df))
    dfs.append(mark_sell_outliers_and_five_pct(orders_df))

    concat_df = pd.concat(
        list(filter(lambda df: df is not None, dfs)),
        ignore_index=True,
    )
    return concat_df


def aggregate_order_stats(orders_df, prefix=None):
    orders_df = orders_df[~orders_df["outlier"]]
    orders_df["value"] = orders_df["volume_remain"] * orders_df["price"]

    results = orders_df.groupby(
        ["region_id", "type_id", "is_buy_order", "last_modified"]
    ).agg(
        order_count=("order_id", "count"),
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
    results = results.reset_index().set_index(
        ["region_id", "type_id", "is_buy_order", "last_modified"]
    )

    return results


def aggregate_five_pct_order_stats(orders_df):
    orders_df = orders_df[orders_df["five_pct"]]
    orders_df["value"] = orders_df["volume_remain"] * orders_df["price"]
    results = orders_df.groupby(
        ["region_id", "type_id", "is_buy_order", "last_modified"]
    ).agg(
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
    results = results.reset_index().set_index(
        ["region_id", "type_id", "is_buy_order", "last_modified"]
    )
    return results


def aggregate_trade_stats(orders_df, prefix=None):
    results = orders_df.groupby(
        ["region_id", "type_id", "is_buy_order", "last_modified"]
    ).agg(
        order_count=("order_id", "count"),
        price_min=("price", np.min),
        price_max=("price", np.max),
        price_avg=("price", np.mean),
        price_std=("price", np.std),
        price_var=("price", np.var),
        price_med=("price", np.median),
        value_sum=("value_traded", np.sum),
        value_min=("value_traded", np.min),
        value_max=("value_traded", np.max),
        value_avg=("value_traded", np.mean),
        value_std=("value_traded", np.std),
        value_var=("value_traded", np.var),
        value_med=("value_traded", np.median),
        volume_sum=("volume_traded", np.sum),
        volume_min=("volume_traded", np.min),
        volume_max=("volume_traded", np.max),
        volume_avg=("volume_traded", np.mean),
        volume_std=("volume_traded", np.std),
        volume_var=("volume_traded", np.var),
        volume_med=("volume_traded", np.median),
    )
    results = results.reset_index().set_index(
        ["region_id", "type_id", "is_buy_order", "last_modified"]
    )

    return results


def mark_buy_outliers_and_five_pct(orders_df):
    buy_orders_df = orders_df[orders_df["is_buy_order"]][
        ["order_id", "region_id", "type_id", "price", "volume_remain", "last_modified"]
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
        ["order_id", "region_id", "type_id", "price", "volume_remain", "last_modified"]
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

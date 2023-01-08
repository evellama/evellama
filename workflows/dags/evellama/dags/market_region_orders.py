from datetime import timedelta

import pendulum
from airflow.decorators import dag, task, task_group
from airflow.utils.dag_parsing_context import get_parsing_context
from airflow.operators.empty import EmptyOperator
from evellama.market import MARKET_REGIONS
from evellama.logging import info
from evellama.market.depths import (
    transform_and_load_exchange_depths,
    transform_and_load_region_depths,
)
from evellama.market.quotes import (
    transform_and_load_exchange_quotes,
    transform_and_load_region_quotes,
)
from evellama.market.stats import (
    transform_and_load_region_stats,
    transform_and_load_exchange_stats,
)
from evellama.market.trades import (
    extract_region_trades,
    load_region_trades_db,
    transform_and_load_exchange_trade_flows,
    transform_and_load_region_trade_flows,
)
from evellama.market.orders import extract_all_region_orders, load_region_orders_db
from evellama.data import DATA_BUCKET_RAW


@dag(
    dag_id="market_region_orders",
    schedule="*/1 * * * *",
    dagrun_timeout=timedelta(seconds=600),
    start_date=pendulum.datetime(2022, 12, 14, tz="UTC"),
    catchup=False,
    tags=["evellama", "market_region_orders"],
)
def market_region_orders():
    @task(task_id="extract_orders", max_active_tis_per_dag=1)
    def task_extract_orders():
        return extract_all_region_orders()

    @task(task_id="load_orders_db", retries=3)
    def task_load_orders_db(extracted_orders):
        # return load_region_orders_db(extracted_orders)
        return extracted_orders

    @task_group(group_id="transform_and_load_depths")
    def group_transform_and_load_depths(extracted_orders):
        @task(task_id="transform_and_load_exchange_depths", retries=3)
        def task_transform_and_load_exchange_depths(extracted_orders):
            return transform_and_load_exchange_depths(extracted_orders)

        @task(
            task_id="transform_and_load_region_depths",
            retries=3,
            max_active_tis_per_dag=3,
        )
        def task_transform_and_load_region_depths(extracted_orders):
            return transform_and_load_region_depths(extracted_orders)

        return {
            "exchange_depths": task_transform_and_load_exchange_depths(
                extracted_orders
            ),
            "region_depths": task_transform_and_load_region_depths(extracted_orders),
        }

    @task_group(group_id="transform_and_load_quotes")
    def group_transform_and_load_quotes(extracted_orders):
        @task(task_id="transform_and_load_exchange_quotes", retries=3)
        def task_transform_and_load_exchange_quotes(extracted_orders):
            return transform_and_load_exchange_quotes(extracted_orders)

        @task(task_id="transform_and_load_region_quotes", retries=3)
        def task_transform_and_load_region_quotes(extracted_orders):
            return transform_and_load_region_quotes(extracted_orders)

        return {
            "exchange_quotes": task_transform_and_load_exchange_quotes(
                extracted_orders
            ),
            "region_quotes": task_transform_and_load_region_quotes(extracted_orders),
        }

    @task_group(group_id="extract_transform_and_load_trades")
    def group_extract_transform_and_load_trades(extracted_orders):
        @task(task_id="extract_trades", retries=3)
        def task_extract_trades(extracted_orders):
            return extract_region_trades(extracted_orders)

        @task(task_id="load_trades_db", retries=3)
        def task_load_trades_db(extracted_trades):
            return load_region_trades_db(extracted_trades)

        @task(task_id="transform_and_load_exchange_trade_flows", retries=3)
        def task_transform_and_load_exchange_trade_flows(extracted_trades):
            return transform_and_load_exchange_trade_flows(extracted_trades)

        @task(task_id="transform_and_load_region_trade_flows", retries=3)
        def task_transform_and_load_region_trade_flows(extracted_trades):
            return transform_and_load_region_trade_flows(extracted_trades)

        extracted_trades = task_extract_trades(extracted_orders)

        # task_load_trades_db(extracted_trades)

        return {
            "exchange_trade_flows": task_transform_and_load_exchange_trade_flows(
                extracted_trades
            ),
            "region_trade_flows": task_transform_and_load_region_trade_flows(
                extracted_trades
            ),
            "trade_orders": extracted_trades,
        }

    @task_group(group_id="transform_and_load_stats")
    def group_transform_and_load_stats(extracted_orders, extracted_trade_orders):
        @task(task_id="transform_and_load_exchange_stats", retries=3)
        def task_transform_and_load_exchange_stats(
            extracted_orders, extracted_trade_orders
        ):
            return transform_and_load_exchange_stats(
                extracted_orders, extracted_trade_orders
            )

        @task(task_id="transform_and_load_region_stats", retries=3)
        def task_transform_and_load_region_stats(
            extracted_orders, extracted_trade_orders
        ):
            return transform_and_load_region_stats(
                extracted_orders, extracted_trade_orders
            )

        return {
            "exchange_stats": task_transform_and_load_exchange_stats(
                extracted_orders, extracted_trade_orders
            ),
            "region_stats": task_transform_and_load_region_stats(
                extracted_orders, extracted_trade_orders
            ),
        }

    extracted_orders = task_extract_orders()

    task_load_orders_db(extracted_orders)
    group_transform_and_load_depths(extracted_orders)
    group_transform_and_load_quotes(extracted_orders)
    trades = group_extract_transform_and_load_trades(extracted_orders)
    group_transform_and_load_stats(extracted_orders, trades["trade_orders"])


market_region_orders()

from datetime import timedelta

import pendulum
from airflow import DAG
from airflow.decorators import task
from evellama.data import DATA_BUCKET_STAGE

with DAG(
    dag_id="market_region_orders_5m",
    schedule_interval="*/5 * * * *",
    dagrun_timeout=timedelta(seconds=300),
    start_date=pendulum.datetime(2023, 1, 2, tz="UTC"),
    catchup=True,
    tags=["evellama"],
    max_active_runs=1,
):

    @task(task_id="extract_orders")
    def task_extract_orders(**kwargs):
        timestamp = pendulum.instance(kwargs["logical_date"])
        print(timestamp)
        return {}

    @task(task_id="transform_and_load_universe_depths")
    def task_transform_and_load_universe_depths(extracted_orders):
        pass

    @task(task_id="transform_and_load_universe_quotes")
    def task_transform_and_load_universe_quotes(extracted_orders):
        pass

    @task(task_id="transform_and_load_universe_trade_flow")
    def task_transform_and_load_universe_trade_flow(extracted_orders):
        pass

    @task(task_id="transform_and_load_universe_stats")
    def task_transform_and_load_universe_stats(extracted_orders):
        pass

    extracted_orders = task_extract_orders()

    task_transform_and_load_universe_depths(extracted_orders)
    task_transform_and_load_universe_quotes(extracted_orders)
    task_transform_and_load_universe_stats(extracted_orders)
    task_transform_and_load_universe_trade_flow(extracted_orders)

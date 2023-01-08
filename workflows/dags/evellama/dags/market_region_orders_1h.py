from datetime import timedelta

import pendulum
from airflow import DAG
from airflow.decorators import task

with DAG(
    dag_id="market_region_orders_1h",
    schedule_interval="0 * * * *",
    dagrun_timeout=timedelta(seconds=300),
    start_date=pendulum.datetime(2022, 12, 14, tz="UTC"),
    catchup=False,
    tags=["evellama"],
    max_active_runs=1,
):

    @task
    def aggregate():
        # TODO: Create 1-hour bars for all regions and hubs
        pass

    aggregate()

import concurrent.futures
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor

import pandas as pd
import pendulum
import requests
from airflow.models import Variable
from evellama.data import DATA_BUCKET_RAW, path_partition, path_timestamp, s3
from evellama.esi import ESI
from evellama.logging import critical, debug, error, info, warning
from evellama.market import MARKET_REGIONS, MARKET_REGION_IDS
from evellama.types import MARKET_ORDER_RANGE_DTYPE
from requests.exceptions import HTTPError
from sqlalchemy import create_engine
import psycopg2
import io


def extract_all_region_orders():
    results = dict()
    with ProcessPoolExecutor() as exe:
        futures = {exe.submit(extract_region_orders, r): r for r in MARKET_REGION_IDS}
        for future in concurrent.futures.as_completed(futures):
            region_id = futures[future]
            try:
                path = future.result()
                if path:
                    results[region_id] = path
                    info(
                        f"Extracted order(s) for region {region_id} and loaded to {path}"
                    )
            except HTTPError as exc:
                error(
                    f"HTTP error fetching region {region_id}, will retry on next run",
                    exc,
                )
            except Exception as exc:
                error(f"Critical error fetching region {region_id}: ", exc)
                raise (exc)

    info(f"Extracted orders for {len(results)} region(s)")

    return results


def extract_region_orders(region_id):
    esi = ESI()
    res = esi.get_market_region_orders(region_id)
    last_modified = pendulum.parse(res.headers.get("last-modified"), strict=False)

    if res.from_cache:
        if orders_persisted(region_id, last_modified):
            info(
                f"Response for first page is still cached and orders have already been loaded for {region_id} at {last_modified}"
            )
            return
        else:
            warning(
                f"Response is cached but orders have not been loaded for region {region_id} at {last_modified}"
            )

    data = res.json()
    if not data:
        info(
            f"No orders for region {region_id} ({MARKET_REGIONS[region_id]} at {last_modified}"
        )
        return

    page_dfs = [pd.DataFrame.from_dict(data)]
    pages = int(res.headers.get("x-pages", 1))
    with ThreadPoolExecutor(max_workers=100) as exe:
        futures = {
            exe.submit(get_region_orders_page, esi, region_id, p): p
            for p in range(2, pages + 1)
        }
        for future in concurrent.futures.as_completed(futures):
            page = futures[future]
            try:
                page_df = future.result()
                page_dfs.append(page_df)
            except Exception as exc:
                error(f"Error fetching page {page} for region {region_id}: ", exc)
                raise

    if not page_dfs:
        info(f"No new orders from region {region_id} at {last_modified}")
        return

    region_df = pd.concat(page_dfs, copy=False, ignore_index=True)

    if region_df.empty:
        info(f"No new orders from region {region_id} at {last_modified}")
        return

    region_df.astype(
        {"issued": "datetime64", "range": MARKET_ORDER_RANGE_DTYPE}, copy=False
    )
    region_df["last_modified"] = pd.Timestamp(last_modified)
    region_df["region_id"] = region_id

    path = load_region_orders_parquet(region_id, last_modified, region_df)
    return path


def orders_persisted(region_id, last_modified):
    path = market_region_orders_path(region_id, last_modified)
    return s3.does_object_exist(path)


def get_region_orders_page(esi, region_id, page):
    res = esi.get_market_region_orders(region_id, page)
    return pd.DataFrame.from_dict(res.json())


def load_region_orders_parquet(region_id, last_modified, orders_df):
    path = market_region_orders_path(region_id, last_modified)
    s3.to_parquet(orders_df, path)
    print(f"Wrote {len(orders_df.index)} order(s) for region {region_id} to {path}")

    return path


def load_region_orders_db(extracted_orders):
    engine = create_engine(Variable.get("EVELLAMA_PUBLIC_MARKET_DATABASE_URL"))
    orders_df = s3.read_parquet(list(extracted_orders.values()))[
        [
            "duration",
            "is_buy_order",
            "issued",
            "last_modified",
            "location_id",
            "min_volume",
            "order_id",
            "price",
            "range",
            "region_id",
            "system_id",
            "type_id",
            "volume_remain",
            "volume_total",
        ]
    ]

    conn = engine.raw_connection()
    cur = conn.cursor()
    output = io.StringIO()
    orders_df.to_csv(output, sep="\t", header=False, index=False)
    output.seek(0)
    output.getvalue()
    cur.copy_expert("COPY market_orders FROM STDIN", output)
    conn.commit()


def send_public_market_orders_heartbeat():
    url = Variable.get(
        "evellama_public_market_orders_heartbeat_webhook_url", default_var=None
    )
    if not url:
        return

    requests.head(url)


def market_region_orders_filename(region_id, last_modified):
    return f"market_region_orders_{region_id}_{path_timestamp(last_modified)}.parquet"


def market_region_orders_prefix(region_id, last_modified):
    return f"market_region_orders/{region_id}/{path_partition(last_modified)}"


def market_region_orders_path(region_id, last_modified):
    filename = market_region_orders_filename(region_id, last_modified)
    prefix = market_region_orders_prefix(region_id, last_modified)
    return f"s3://{DATA_BUCKET_RAW}/{prefix}/{filename}"

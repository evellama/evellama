import awswrangler as wr
import boto3
import redis
from airflow.models import Variable

wr.config.s3_endpoint_url = Variable.get(
    "EVELLAMA_DATA_ENDPOINT_URL", "http://minio:9000"
)

boto3.setup_default_session(
    aws_access_key_id=Variable.get("EVELLAMA_DATA_ACCESS_KEY_ID"),
    aws_secret_access_key=Variable.get("EVELLAMA_DATA_SECRET_ACCESS_KEY"),
)

DATA_BUCKET_RAW = Variable.get("EVELLAMA_DATA_BUCKET_RAW", "evellama-data-raw")
DATA_BUCKET_STAGE = Variable.get("EVELLAMA_DATA_BUCKET_STAGE", "evellama-data-stage")
DATA_BUCKET_ANALYTICS = Variable.get(
    "EVELLAMA_DATA_BUCKET_ANALYTICS", "evellama-data-analytics"
)

DATA_CONNECTION = Variable.get(
    "EVELLAMA_S3_DATA_CONNECTION", default_var="evellama_s3_data_writer"
)

s3 = wr.s3


def path_timestamp(dt):
    return dt.format("YYYYMMDD_X")


def path_partition(dt):
    return dt.format("YYYY/MM/DD")

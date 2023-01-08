import pandas as pd
import pendulum
import re

from evellama.data import DATA_BUCKET_ANALYTICS, DATA_BUCKET_STAGE, s3


def calculate_bars(prefix, timestamp, freq):
    timestamp = pendulum.datetime(year=2023, month=1, day=3, hour=17, minute=15)

    paths = s3.list_objects(
        f"s3://{DATA_BUCKET_STAGE}/{prefix}/{timestamp.format('YYYY/MM/DD')}"
    )
    paths = {
        p: pendulum.from_timestamp(int(re.search("(\d+)\.parquet$", p).group(1)))
        for p in paths
    }
    paths = {
        k: v
        for (k, v) in paths.items()
        if v >= timestamp.subtract(minutes=15) and v < timestamp
    }

    {print(f"{t}: {p}") for (p, t) in paths.items()}
    df = s3.read_parquet(list(paths.keys()))
    idx = pd.DatetimeIndex(df["last_modified"]).floor("5T")
    idx.unique()

    type_dfs = []
    for type_id, type_df in df.groupby("type_id"):
        type_idx = pd.DatetimeIndex(type_df["last_modified"]).floor("5T")
        type_df = type_df.set_index(type_idx)
        rs = type_df.resample(f"{freq}T")
        ohlc = rs["price"].ohlc()
        sums = rs[["value", "volume", "count"]].sum()
        bar = ohlc.join(sums)
        bar["type_id"] = type_id
        type_dfs.append(bar)

    df = pd.concat(type_dfs)
    df.index = df.index + pd.Timedelta(f"{freq} minutes")
    df

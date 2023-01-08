import pandas as pd

from os.path import abspath, dirname

import yaml

try:
    from yaml import CLoader as YAMLLoader
except ImportError:
    from yaml import YAMLLoader

SDE_PATH = abspath("../data/sde")

NAMES = pd.read_parquet("../data/names.parquet")


def find_name(id):
    return NAMES[NAMES["itemID"] == id]["itemName"].values[0]


def load_sde_yaml(path):
    full_path = "/".join([SDE_PATH, path])
    with open(full_path, "r") as f:
        return yaml.load(f, Loader=YAMLLoader)

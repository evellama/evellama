from pandas.api.types import CategoricalDtype

MARKET_ORDER_RANGE_DTYPE = CategoricalDtype(
    categories=[
        "station",
        "region",
        "solarsystem",
        "1",
        "2",
        "3",
        "4",
        "5",
        "10",
        "20",
        "30",
        "40",
    ]
)

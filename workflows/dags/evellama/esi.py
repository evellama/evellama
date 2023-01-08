from airflow.models import Variable
from requests.adapters import HTTPAdapter
from urllib3 import Retry
from cachecontrol import CacheControl
from cachecontrol.caches.redis_cache import RedisCache
import redis
import requests


USER_AGENT = Variable.get("EVELLAMA_USER_AGENT", "EVE Llama/1.0")


class ESI:
    BASE_URL = "https://esi.evetech.net/latest"

    def __init__(self) -> None:
        self.http = self.build_client()

    def check_market_region_orders(self, region_id):
        res = self.http.head(
            f"{self.BASE_URL}/markets/{region_id}/orders/",
            headers={"User-Agent": USER_AGENT},
            params=[("order_type", "all"), ("page", 1)],
        )
        return res

    def get_market_region_orders(self, region_id, page=1):
        res = self.http.get(
            f"{self.BASE_URL}/markets/{region_id}/orders/",
            headers={"User-Agent": USER_AGENT},
            params=sorted([("order_type", "all"), ("page", page)]),
        )
        res.raise_for_status()
        return res

    def get_market_structure_orders(self, structure_id, token, page=1):
        res = self.http.get(
            f"{self.BASE_URL}/markets/structures/{structure_id}/orders/",
            headers={"User-Agent": USER_AGENT, "Authorization": f"Bearer {token}"},
            params=sorted([("order_type", "all"), ("page", page)]),
        )
        res.raise_for_status()
        return res

    def build_client(self):
        redis_cache_pool = redis.ConnectionPool(
            host=Variable.get("EVELLAMA_HTTP_CACHE_HOST", default_var="redis-cache"),
            password=Variable.get("EVELLAMA_HTTP_CACHE_PASSWORD", default_var=None),
            port=6379,
            db=0,
        )
        redis_cache = redis.Redis(connection_pool=redis_cache_pool)
        session = requests.Session()
        adapter = HTTPAdapter(
            max_retries=Retry(
                total=5,
                backoff_factor=1,
                allowed_methods=None,
                status_forcelist=[503, 504],
            ),
            pool_connections=100,
            pool_maxsize=100,
        )
        session.mount("https://", adapter)
        return CacheControl(session, cache=RedisCache(redis_cache))

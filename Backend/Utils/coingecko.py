import httpx
from typing import List

from Config.config import settings
from Utils.redis_cache import cached

HEADERS = {"accept": "application/json"}
if settings.COINGECKO_API_KEY:
    HEADERS["x-cg-demo-api-key"] = settings.COINGECKO_API_KEY


def get_markets(coin_ids: List[str]) -> list:
    """Fetch CoinGecko /coins/markets for a list of ids."""
    if not coin_ids:
        return []
    ids = ",".join(sorted(set(coin_ids)))
    key = f"cg:markets:{ids}"

    def fetch():
        url = f"{settings.COINGECKO_BASE_URL}/coins/markets"
        params = {
            "vs_currency": "usd",
            "ids": ids,
            "order": "market_cap_desc",
            "per_page": 250,
            "page": 1,
            "sparkline": "false",
            "price_change_percentage": "24h",
        }
        with httpx.Client(timeout=10.0, headers=HEADERS) as client:
            r = client.get(url, params=params)
            r.raise_for_status()
            return r.json()

    return cached(key, settings.MARKET_CACHE_TTL, fetch)


def search_coins(query: str) -> list:
    """Search CoinGecko coins by name or symbol. Returns only the 'coins' section."""
    query = query.strip().lower()
    if not query:
        return []
    key = f"cg:search:{query}"

    def fetch():
        url = f"{settings.COINGECKO_BASE_URL}/search"
        with httpx.Client(timeout=10.0, headers=HEADERS) as client:
            r = client.get(url, params={"query": query})
            r.raise_for_status()
            data = r.json()
            return data.get("coins", [])

    return cached(key, settings.SEARCH_CACHE_TTL, fetch)

import httpx
from typing import List

from fastapi import HTTPException, status
from Config.config import settings
from Utils.redis_cache import cached

HEADERS = {"accept": "application/json"}

if settings.COINGECKO_API_KEY:
    HEADERS["x-cg-demo-api-key"] = settings.COINGECKO_API_KEY

# Fetch CoinGecko /coins/markets for a list of ids.
def get_markets(coin_ids: List[str]) -> list:
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

# Search CoinGecko coins by name or symbol
def search_coins(query: str) -> list:
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

# Fetch CoinGecko /coins/{id}/market_chart for the given lookback window.
def get_market_chart(coin_id: str, days: int) -> dict:
    key = f"cg:chart:{coin_id}:{days}"

    def fetch():
        url = f"{settings.COINGECKO_BASE_URL}/coins/{coin_id}/market_chart"
        params = {"vs_currency": "usd", "days": days}
        with httpx.Client(timeout=10.0, headers=HEADERS) as client:
            r = client.get(url, params=params)
            r.raise_for_status()
            return r.json()

    return cached(key, settings.CHART_CACHE_TTL, fetch)

# Ensure coin_slug is a real CoinGecko coin id before it gets stored.
def validate_coin_slug(coin_slug: str) -> None:
    try:
        data = get_markets([coin_slug])
    except httpx.HTTPError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not verify coin against market data, please try again",
        )

    if not any(c.get("id") == coin_slug for c in data):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"'{coin_slug}' is not a recognized coin. Use the id from market search.",
        )

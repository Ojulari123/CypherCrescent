from typing import List
from coingecko_sdk import Coingecko, APIError
from fastapi import HTTPException, status
from Config.config import settings
from Utils.redis_cache import cached

cg = Coingecko(demo_api_key=settings.COINGECKO_API_KEY, environment="demo", base_url=None)

# Error for when CoinGecko is unreachable or returns an error
class MarketDataError(Exception):
    pass

# Fetch CoinGecko for a list of ids
def get_markets(coin_ids: List[str]) -> list:
    if not coin_ids:
        return []
    ids = ",".join(sorted(set(coin_ids)))
    key = f"cg:markets:{ids}"

    def fetch():
        try:
            resp = cg.coins.markets.get(
                vs_currency="usd",
                ids=ids,
                order="market_cap_desc",
                per_page=250,
                page=1,
                sparkline=False,
                price_change_percentage="1h,24h,7d",
            )
        except APIError as e:
            raise MarketDataError(str(e))
        return [item.model_dump(mode="json") for item in resp]

    return cached(key, settings.MARKET_CACHE_TTL, fetch)

# Fetch the top coins by market cap for a given page (no explicit ids).
# CoinGecko returns coins ordered by market cap; there are thousands of coins,
# so this is what backs the Markets page's pagination.
def get_top_markets(page: int = 1, per_page: int = 50) -> list:
    key = f"cg:topmarkets:{page}:{per_page}"

    def fetch():
        try:
            resp = cg.coins.markets.get(
                vs_currency="usd",
                order="market_cap_desc",
                per_page=per_page,
                page=page,
                sparkline=False,
                price_change_percentage="1h,24h,7d",
            )
        except APIError as e:
            raise MarketDataError(str(e))
        return [item.model_dump(mode="json") for item in resp]

    return cached(key, settings.MARKET_CACHE_TTL, fetch)

# Search CoinGecko coins by name or symbol
def search_coins(query: str) -> list:
    query = query.strip().lower()
    if not query:
        return []
    key = f"cg:search:{query}"

    def fetch():
        try:
            resp = cg.search.get(query=query)
        except APIError as e:
            raise MarketDataError(str(e))
        return [coin.model_dump(mode="json") for coin in resp.coins]

    return cached(key, settings.SEARCH_CACHE_TTL, fetch)

# Fetch historical market chart for a coin over the given lookback window (days)
def get_market_chart(coin_id: str, days: int) -> dict:
    key = f"cg:chart:{coin_id}:{days}"

    def fetch():
        try:
            resp = cg.coins.market_chart.get(coin_id, days=str(days), vs_currency="usd")
        except APIError as e:
            raise MarketDataError(str(e))
        return resp.model_dump(mode="json")

    return cached(key, settings.CHART_CACHE_TTL, fetch)

# Ensure coin_slug is a real CoinGecko coin id before it gets stored
def validate_coin_slug(coin_slug: str) -> None:
    try:
        data = get_markets([coin_slug])
    except MarketDataError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not verify coin against market data, please try again",
        )

    if not any(c.get("id") == coin_slug for c in data):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"'{coin_slug}' is not a recognized coin. Use the id from market search.",
        )

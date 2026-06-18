import httpx
from Schemas.watchlistSchema import WatchlistItemWithMarket
from Utils.coingecko import get_markets
from Utils.dashboard import to_decimal

# Combine one Watchlist row with its CoinGecko market data.
def enrich_watchlist_item(item, market_by_id):
    market = market_by_id.get(item.coin_slug, {})
    symbol = market.get("symbol")
    return {
        "id": item.id,
        "coin_slug": item.coin_slug,
        "created_at": item.created_at,
        "name": market.get("name"),
        "symbol": symbol.upper() if symbol else None,
        "image": market.get("image"),
        "current_price": to_decimal(market.get("current_price")),
        "market_cap": to_decimal(market.get("market_cap")),
        "price_change_percentage_24h": to_decimal(market.get("price_change_percentage_24h")),
    }

# Fetch live market data for the given watchlist rows and shape the response.
def build_watchlist_response(items):
    if not items:
        return []

    try:
        market_data = get_markets([i.coin_slug for i in items])
    except httpx.HTTPError:
        market_data = []

    market_by_id = {m["id"]: m for m in market_data}
    return [WatchlistItemWithMarket.model_validate(enrich_watchlist_item(i, market_by_id)) for i in items]

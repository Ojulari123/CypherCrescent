from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from tables import Watchlist, User
from Utils.dashboard import to_decimal

def get_watchlist_item_or_404(item_id: int, current_user: User, db: Session) -> Watchlist:
    item = db.query(Watchlist).filter(Watchlist.id == item_id, Watchlist.user_id == current_user.id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Watchlist item not found")
    return item

def enrich_watchlist_item(item, market_by_id):
    """Combine one Watchlist row with its CoinGecko market data."""
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

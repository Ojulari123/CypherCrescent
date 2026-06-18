import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from tables import *
from Schemas.watchlistSchema import *
from Utils.security import get_current_user
from Utils.coingecko import get_markets, validate_coin_slug
from Utils.watchlist import get_watchlist_item_or_404, enrich_watchlist_item

watchlist_router = APIRouter()

# Add coin to watchlist
@watchlist_router.post("", response_model=WatchlistResponse, status_code=status.HTTP_201_CREATED)
def add_to_watchlist(payload: WatchlistCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    existing = db.query(Watchlist).filter(Watchlist.user_id == current_user.id, Watchlist.coin_slug == payload.coin_slug).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"{payload.coin_slug} is already in your watchlist.")

    validate_coin_slug(payload.coin_slug)

    item = Watchlist(user_id=current_user.id, coin_slug=payload.coin_slug)
    db.add(item)
    db.commit()
    db.refresh(item)
    return WatchlistResponse.model_validate(item)

# View watchlist (enriched with live market data)
@watchlist_router.get("", response_model=list[WatchlistItemWithMarket], status_code=status.HTTP_200_OK)
def list_watchlist(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    items = db.query(Watchlist).filter(Watchlist.user_id == current_user.id).order_by(Watchlist.created_at.desc(), Watchlist.id.desc()).all()
    if not items:
        return []

    try:
        market_data = get_markets([i.coin_slug for i in items])
    except httpx.HTTPError:
        market_data = []

    market_by_id = {m["id"]: m for m in market_data}
    return [WatchlistItemWithMarket.model_validate(enrich_watchlist_item(i, market_by_id)) for i in items]

# Remove coin from watchlist
@watchlist_router.delete("/{item_id}", status_code=status.HTTP_200_OK)
def remove_from_watchlist(item_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = get_watchlist_item_or_404(item_id, current_user, db)
    db.delete(item)
    db.commit()
    return {"message": "Removed from watchlist"}

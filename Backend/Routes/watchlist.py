from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from tables import get_db, User, Watchlist
from Schemas.watchlistSchema import *
from Utils.security import get_current_user
from Utils.coingecko import validate_coin_slug
from Utils.watchlist import build_watchlist_response

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
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"{payload.coin_slug} is already in your watchlist.")
    db.refresh(item)
    return WatchlistResponse.model_validate(item)

# View watchlist (enriched with live market data)
@watchlist_router.get("", response_model=list[WatchlistItemWithMarket], status_code=status.HTTP_200_OK)
def list_watchlist(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    items = db.query(Watchlist).filter(Watchlist.user_id == current_user.id).order_by(Watchlist.created_at.desc(), Watchlist.id.desc()).all()
    return build_watchlist_response(items)

# Remove coin from watchlist
@watchlist_router.delete("/{item_id}", status_code=status.HTTP_200_OK)
def remove_from_watchlist(item_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = db.query(Watchlist).filter(Watchlist.id == item_id, Watchlist.user_id == current_user.id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Watchlist item not found")

    db.delete(item)
    db.commit()
    return {"message": "Removed from watchlist"}

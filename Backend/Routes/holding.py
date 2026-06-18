from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from tables import get_db, User, Holding
from Schemas.holdingSchema import *
from Utils.security import get_current_user
from Utils.coingecko import validate_coin_slug

holding_router = APIRouter()

# Add holding
@holding_router.post("", response_model=HoldingResponse, status_code=status.HTTP_201_CREATED)
def add_holding(payload: HoldingCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    existing = db.query(Holding).filter(Holding.user_id == current_user.id, Holding.coin_slug == payload.coin_slug).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"You already hold {payload.coin_slug}.")

    validate_coin_slug(payload.coin_slug)

    holding = Holding(
        user_id=current_user.id,
        coin_slug=payload.coin_slug,
        quantity=payload.quantity,
        buy_price=payload.buy_price,
    )
    db.add(holding)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"You already hold {payload.coin_slug}.")
    db.refresh(holding)
    return HoldingResponse.model_validate(holding)

# List holdings
@holding_router.get("", response_model=list[HoldingResponse], status_code=status.HTTP_200_OK)
def list_holdings(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    holdings = db.query(Holding).filter(Holding.user_id == current_user.id).order_by(Holding.created_at.desc(), Holding.id.desc()).all()
    return [HoldingResponse.model_validate(h) for h in holdings]

# Get one holding
@holding_router.get("/{holding_id}", response_model=HoldingResponse, status_code=status.HTTP_200_OK)
def get_holding(holding_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    holding = db.query(Holding).filter(Holding.id == holding_id, Holding.user_id == current_user.id).first()
    if not holding:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Holding not found")
    return HoldingResponse.model_validate(holding)

# Update holding
@holding_router.patch("/{holding_id}", response_model=HoldingResponse, status_code=status.HTTP_200_OK)
def update_holding(holding_id: int, payload: HoldingUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    holding = db.query(Holding).filter(Holding.id == holding_id, Holding.user_id == current_user.id).first()
    if not holding:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Holding not found")

    if payload.quantity is not None:
        holding.quantity = payload.quantity
    if payload.buy_price is not None:
        holding.buy_price = payload.buy_price

    db.commit()
    db.refresh(holding)
    return HoldingResponse.model_validate(holding)

# Delete holding
@holding_router.delete("/{holding_id}", status_code=status.HTTP_200_OK)
def delete_holding(holding_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    holding = db.query(Holding).filter(Holding.id == holding_id, Holding.user_id == current_user.id).first()
    if not holding:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Holding not found")

    db.delete(holding)
    db.commit()
    return {"message": "Holding deleted"}

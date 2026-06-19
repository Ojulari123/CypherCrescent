from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from tables import get_db, User, PriceAlert
from Schemas.alertSchema import AlertCreate, AlertUpdate, AlertResponse
from Utils.security import get_current_user
from Utils.coingecko import validate_coin_slug

alert_router = APIRouter()

ALERT_LIMIT = 10

@alert_router.post("", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
def create_alert(payload: AlertCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    active_count = db.query(PriceAlert).filter(PriceAlert.user_id == current_user.id, PriceAlert.triggered == False).count()
    if active_count >= ALERT_LIMIT:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"You can have at most {ALERT_LIMIT} active alerts. Delete one to add another.")

    validate_coin_slug(payload.coin_slug)

    alert = PriceAlert(
        user_id=current_user.id,
        coin_slug=payload.coin_slug,
        target_price=payload.target_price,
        direction=payload.direction,
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return AlertResponse.model_validate(alert)

@alert_router.get("", response_model=list[AlertResponse], status_code=status.HTTP_200_OK)
def list_alerts(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    alerts = (db.query(PriceAlert).filter(PriceAlert.user_id == current_user.id).order_by(PriceAlert.created_at.desc()).all())
    return [AlertResponse.model_validate(a) for a in alerts]

@alert_router.patch("/{alert_id}", response_model=AlertResponse, status_code=status.HTTP_200_OK)
def update_alert(alert_id: int, payload: AlertUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    alert = db.query(PriceAlert).filter(PriceAlert.id == alert_id, PriceAlert.user_id == current_user.id).first()
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    if alert.triggered:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot edit a triggered alert")
    if payload.target_price is not None:
        alert.target_price = payload.target_price
    if payload.direction is not None:
        alert.direction = payload.direction
    db.commit()
    db.refresh(alert)
    return AlertResponse.model_validate(alert)

@alert_router.post("/{alert_id}/reactivate", response_model=AlertResponse, status_code=status.HTTP_200_OK)
def reactivate_alert(alert_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    alert = db.query(PriceAlert).filter(PriceAlert.id == alert_id, PriceAlert.user_id == current_user.id).first()
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    if not alert.triggered:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Alert is already active")
    active_count = db.query(PriceAlert).filter(PriceAlert.user_id == current_user.id, PriceAlert.triggered == False).count()
    if active_count >= ALERT_LIMIT:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"You can have at most {ALERT_LIMIT} active alerts. Delete one to reactivate this alert.")
    alert.triggered = False
    alert.triggered_at = None
    db.commit()
    db.refresh(alert)
    return AlertResponse.model_validate(alert)

@alert_router.delete("/{alert_id}", status_code=status.HTTP_200_OK)
def delete_alert(alert_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    alert = db.query(PriceAlert).filter(PriceAlert.id == alert_id, PriceAlert.user_id == current_user.id).first()
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    db.delete(alert)
    db.commit()
    return {"message": "Alert deleted"}

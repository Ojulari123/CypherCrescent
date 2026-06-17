from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from tables import Holding, User


def get_holding_or_404(holding_id: int, current_user: User, db: Session) -> Holding:
    holding = db.query(Holding).filter(Holding.id == holding_id, Holding.user_id == current_user.id).first()
    if not holding:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Holding not found")
    return holding

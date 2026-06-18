import logging
from typing import Optional
from fastapi import Request
from sqlalchemy.orm import Session
from tables import ActivityLog

logger = logging.getLogger(__name__)

# Record a security-relevant event for a user. E.g. (a logging failure). It must never break the action the user actually performed.
def record_activity(db: Session, user_id: int, event: str, request: Optional[Request] = None) -> None:
    ip_address = None
    user_agent = None
    if request is not None:
        ip_address = request.client.host if request.client else None
        agent = request.headers.get("user-agent")
        user_agent = agent[:400] if agent else None

    try:
        db.add(ActivityLog(user_id=user_id, event=event, ip_address=ip_address, user_agent=user_agent))
        db.commit()
    except Exception as e:
        db.rollback()
        logger.warning("Failed to record activity '%s' for user %s: %s", event, user_id, e)

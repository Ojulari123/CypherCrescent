from sqlalchemy.orm import Session
from tables import User, Holding, Watchlist, ActivityLog
from Utils.cloudinary import delete_image_from_cloudinary

def cascade_delete_user(user: User, db: Session):
    user_id = user.id

    if user.profile_photo_url:
        delete_image_from_cloudinary(user.profile_photo_url)

    db.query(Holding).filter(Holding.user_id == user_id).delete(synchronize_session=False)

    db.query(Watchlist).filter(Watchlist.user_id == user_id).delete(synchronize_session=False)

    db.query(ActivityLog).filter(ActivityLog.user_id == user_id).delete(synchronize_session=False)

    db.delete(user)

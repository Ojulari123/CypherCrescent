from sqlalchemy.orm import Session
from tables import User, Holding, Watchlist
from Utils.cloudinary import delete_image_from_cloudinary


def cascade_delete_user(user: User, db: Session):
    """Delete a user and all their related data in the correct order."""
    user_id = user.id

    # 1. Profile photo (Cloudinary)
    if user.profile_photo_url:
        delete_image_from_cloudinary(user.profile_photo_url)

    # 2. Holdings
    db.query(Holding).filter(Holding.user_id == user_id).delete(synchronize_session=False)

    # 3. Watchlist
    db.query(Watchlist).filter(Watchlist.user_id == user_id).delete(synchronize_session=False)

    # 4. Delete the user
    db.delete(user)

import logging
from fastapi import APIRouter, Depends, HTTPException, status, Form, Request, File, UploadFile, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from tables import *
from Schemas.userSchema import *
from Utils.security import *
from Utils.email_token import *
from Utils.email import send_verification, send_password_reset
from Utils.cloudinary import upload_image_to_cloudinary, delete_image_from_cloudinary, ALLOWED_IMAGE_TYPES
from Utils.user import cascade_delete_user
from Utils.rate_limit import limiter
from Config.config import settings

logger = logging.getLogger(__name__)
user_router = APIRouter()

# Create User
@user_router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
def register_users(request: Request, payload: UserCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    validate_password(payload.password)

    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An account with this email already exists")

    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        first_name=payload.first_name,
        last_name=payload.last_name,
        display_name=payload.display_name,
        email_verified=False,
    )
    try:
        db.add(user)
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An account with this email already exists")
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create account")

    background_tasks.add_task(send_verification, user.email, user.first_name)

    access_token = create_access_token({"user_id": user.id, "tv": user.token_version})

    return TokenResponse(
        access_token=access_token,
        user=UserResponse.model_validate(user),
    )

# User Login
@user_router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
@limiter.limit("5/minute")
async def login_user(request: Request, payload: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()

    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    token = create_access_token({"user_id": user.id, "tv": user.token_version})
    return TokenResponse(access_token=token, user=UserResponse.model_validate(user))

# OAuth2 token (Swagger)
@user_router.post("/token", response_model=TokenResponse, status_code=status.HTTP_200_OK)
@limiter.limit("5/minute")
def login_for_token(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()

    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    token = create_access_token({"user_id": user.id, "tv": user.token_version})
    return TokenResponse(access_token=token, user=UserResponse.model_validate(user))

# Refresh Token
@user_router.post("/refresh", status_code=status.HTTP_200_OK)
def refresh_token(current_user: User = Depends(get_current_user)):
    token = create_access_token({"user_id": current_user.id, "tv": current_user.token_version})
    return {"access_token": token, "token_type": "bearer"}

# Verify email
@user_router.get("/verify-email", status_code=status.HTTP_200_OK)
def verify_email(token: str, db: Session = Depends(get_db)):
    email = decode_email_verification_token(token)

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.email_verified:
        return {"message": "Email already verified"}

    user.email_verified = True
    db.commit()

    access_token = create_access_token({"user_id": user.id, "tv": user.token_version})
    return TokenResponse(access_token=access_token, user=UserResponse.model_validate(user))

# Re-send verification
@user_router.post("/resend-verification", status_code=status.HTTP_200_OK)
@limiter.limit("3/minute")
def resend_verification(request: Request, background_tasks: BackgroundTasks, email: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()

    if user and not user.email_verified:
        background_tasks.add_task(send_verification, user.email, user.first_name)

    return {"message": "If an unverified account exists with that email, a verification link has been sent."}

# Forgot Password
@user_router.post("/forgot-password", status_code=status.HTTP_200_OK)
@limiter.limit("3/minute")
def forgot_password(request: Request, payload: ForgotPasswordRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if user:
        background_tasks.add_task(send_password_reset, user.email, user.first_name)

    return {"message": "If an account exists with that email, a reset link has been sent."}

# Reset Password
@user_router.post("/reset-password", status_code=status.HTTP_200_OK)
@limiter.limit("5/minute")
def reset_password(request: Request, payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    email = decode_password_reset_token(payload.token)

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    validate_password(payload.new_password)

    if verify_password(payload.new_password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="New password must be different from your current password")

    user.password_hash = hash_password(payload.new_password)
    user.token_version = (user.token_version or 0) + 1
    db.commit()

    return {"message": "Password has been reset successfully. You can now log in."}

# Get current user
@user_router.get("/me", response_model=UserResponse, status_code=status.HTTP_200_OK)
def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)

# Update current user profile
@user_router.patch("/me", response_model=UserResponse)
def update_me(payload: UserUpdate, background_tasks: BackgroundTasks, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if payload.email and payload.email != current_user.email:
        existing = db.query(User).filter(User.email == payload.email).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An account with this email already exists")
        current_user.email = payload.email
        current_user.email_verified = False
        background_tasks.add_task(send_verification, payload.email, current_user.first_name)

    if payload.first_name:
        current_user.first_name = payload.first_name
    if payload.last_name:
        current_user.last_name = payload.last_name
    if payload.display_name is not None:
        current_user.display_name = payload.display_name
    db.commit()
    db.refresh(current_user)
    return UserResponse.model_validate(current_user)

# Change password
@user_router.put("/me/password", response_model=TokenResponse, status_code=status.HTTP_200_OK)
def change_password(payload: PasswordChange, db: Session = Depends(get_db),current_user: User = Depends(get_current_user)):
    if not verify_password(payload.current_password, current_user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Current password is incorrect")

    if payload.new_password == payload.current_password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="New password must be different from your current password")

    validate_password(payload.new_password)

    current_user.password_hash = hash_password(payload.new_password)
    current_user.token_version = (current_user.token_version or 0) + 1
    db.commit()
    db.refresh(current_user)

    token = create_access_token({"user_id": current_user.id, "tv": current_user.token_version})
    return TokenResponse(access_token=token, user=UserResponse.model_validate(current_user))

# Upload profile photo
@user_router.post("/me/profile-photo", status_code=status.HTTP_200_OK)
async def upload_profile_photo(file: UploadFile = File(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail="Invalid image type. Allowed: JPEG, PNG, WebP")

    old_photo_url = current_user.profile_photo_url

    image_url = upload_image_to_cloudinary(file, folder=f"userDP/{current_user.id}")
    current_user.profile_photo_url = image_url
    db.commit()

    if old_photo_url:
        delete_image_from_cloudinary(old_photo_url)

    return {"profile_photo_url": image_url}

# Delete profile photo
@user_router.delete("/me/profile-photo", status_code=status.HTTP_200_OK)
def delete_profile_photo(db: Session = Depends(get_db),current_user: User = Depends(get_current_user)):
    if not current_user.profile_photo_url:
        raise HTTPException(status_code=400, detail="No profile photo to delete")

    delete_image_from_cloudinary(current_user.profile_photo_url)
    current_user.profile_photo_url = None
    db.commit()

    return {"message": "Profile photo removed"}

# Delete account
@user_router.delete("/me", status_code=status.HTTP_200_OK)
def delete_me(payload: DeleteAccount, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not verify_password(payload.password, current_user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Password is incorrect")

    cascade_delete_user(current_user, db)
    db.commit()
    return {"message": "Account deleted successfully."}

# Logout
@user_router.post("/logout", status_code=status.HTTP_200_OK)
def logout(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    current_user.token_version = (current_user.token_version or 0) + 1
    db.commit()
    return {"message": "Logged out successfully."}

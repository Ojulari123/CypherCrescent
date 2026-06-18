from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, field_validator
from typing import Optional

def normalize_email(v):
    return v.strip().lower() if v else v

# Request
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    display_name: Optional[str] = None

    _normalize_email = field_validator("email")(normalize_email)

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v

class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    display_name: Optional[str] = None
    email: Optional[EmailStr] = None

    _normalize_email = field_validator("email")(normalize_email)

    @field_validator("first_name", "last_name")
    @classmethod
    def not_blank(cls, v):
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("cannot be empty")
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str

    _normalize_email = field_validator("email")(normalize_email)

class PasswordChange(BaseModel):
    current_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def password_min_length(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

    _normalize_email = field_validator("email")(normalize_email)

class ResendVerificationRequest(BaseModel):
    email: EmailStr

    _normalize_email = field_validator("email")(normalize_email)

class DeleteAccount(BaseModel):
    password: str

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def password_min_length(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v

class TwoFactorCode(BaseModel):
    code: str

class TwoFactorVerify(BaseModel):
    challenge_token: str
    code: str

class PasswordChangeVerify(BaseModel):
    code: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def password_min_length(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v

# Response    
class UserResponse(BaseModel):
    id: int
    email: str
    first_name: str
    last_name: str
    display_name: Optional[str] = None
    email_verified: bool
    two_factor_enabled: bool
    profile_photo_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
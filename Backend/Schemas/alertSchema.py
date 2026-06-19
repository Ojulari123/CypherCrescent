from datetime import datetime
from decimal import Decimal
from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, field_validator

class AlertCreate(BaseModel):
    coin_slug: str
    target_price: Decimal
    direction: Literal["above", "below"]

    @field_validator("coin_slug")
    @classmethod
    def normalize_slug(cls, v):
        v = v.strip().lower()
        if not v:
            raise ValueError("coin_slug cannot be empty")
        return v

    @field_validator("target_price")
    @classmethod
    def price_positive(cls, v):
        if v <= 0:
            raise ValueError("Target price must be greater than 0")
        return v

class AlertUpdate(BaseModel):
    target_price: Optional[Decimal] = None
    direction: Optional[Literal["above", "below"]] = None

    @field_validator("target_price")
    @classmethod
    def price_positive(cls, v):
        if v is not None and v <= 0:
            raise ValueError("Target price must be greater than 0")
        return v

class AlertResponse(BaseModel):
    id: int
    coin_slug: str
    target_price: Decimal
    direction: str
    triggered: bool
    triggered_at: Optional[datetime]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional

# Request
class HoldingCreate(BaseModel):
    coin_slug: str
    quantity: Decimal
    buy_price: Decimal

    @field_validator("coin_slug")
    @classmethod
    def normalize_slug(cls, v):
        v = v.strip().lower()
        if not v:
            raise ValueError("coin_slug cannot be empty")
        return v

    @field_validator("quantity")
    @classmethod
    def quantity_positive(cls, v):
        if v <= 0:
            raise ValueError("Quantity must be greater than 0")
        return v

    @field_validator("buy_price")
    @classmethod
    def buy_price_positive(cls, v):
        if v <= 0:
            raise ValueError("Buy price must be greater than 0")
        return v

class HoldingUpdate(BaseModel):
    quantity: Optional[Decimal] = None
    buy_price: Optional[Decimal] = None

    @field_validator("quantity")
    @classmethod
    def quantity_positive(cls, v):
        if v is not None and v <= 0:
            raise ValueError("Quantity must be greater than 0")
        return v

    @field_validator("buy_price")
    @classmethod
    def buy_price_positive(cls, v):
        if v is not None and v <= 0:
            raise ValueError("Buy price must be greater than 0")
        return v

# Response
class HoldingResponse(BaseModel):
    id: int
    coin_slug: str
    quantity: Decimal
    buy_price: Decimal
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

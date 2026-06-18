from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional

# Request
class WatchlistCreate(BaseModel):
    coin_slug: str

    @field_validator("coin_slug")
    @classmethod
    def normalize_slug(cls, v):
        v = v.strip().lower()
        if not v:
            raise ValueError("coin_slug cannot be empty")
        return v

# Response
class WatchlistResponse(BaseModel):
    id: int
    coin_slug: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class WatchlistItemWithMarket(BaseModel):
    id: int
    coin_slug: str
    created_at: datetime
    name: Optional[str] = None
    symbol: Optional[str] = None
    image: Optional[str] = None
    current_price: Optional[Decimal] = None
    market_cap: Optional[Decimal] = None
    price_change_percentage_24h: Optional[Decimal] = None

    model_config = ConfigDict(from_attributes=True)

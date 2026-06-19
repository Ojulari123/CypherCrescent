from typing import Optional, List
from decimal import Decimal
from pydantic import BaseModel, ConfigDict
import enum

# Enum
class ChartRange(str, enum.Enum):
    DAY = "24h"
    WEEK = "7d"
    MONTH = "30d"

# Request
class CoinMarket(BaseModel):
    id: str
    symbol: str
    name: str
    image: Optional[str] = None
    market_cap_rank: Optional[int] = None
    current_price: Optional[Decimal] = None
    market_cap: Optional[Decimal] = None
    price_change_percentage_1h_in_currency: Optional[Decimal] = None
    price_change_percentage_24h: Optional[Decimal] = None
    price_change_percentage_7d_in_currency: Optional[Decimal] = None

    model_config = ConfigDict(from_attributes=True)

class ChartPoint(BaseModel):
    timestamp: int
    price: float

class HoldingWithMarket(BaseModel):
    id: int
    coin_slug: str
    quantity: Decimal
    buy_price: Decimal
    name: Optional[str] = None
    symbol: Optional[str] = None
    image: Optional[str] = None
    current_price: Optional[Decimal] = None
    market_cap: Optional[Decimal] = None
    price_change_percentage_24h: Optional[Decimal] = None
    value: Optional[Decimal] = None
    cost_basis: Decimal
    pl: Optional[Decimal] = None
    pl_percent: Optional[Decimal] = None

    model_config = ConfigDict(from_attributes=True)

class Performer(BaseModel):
    coin_slug: str
    name: Optional[str] = None
    pl_percent: Decimal

# Response
class ChartResponse(BaseModel):
    coin_id: str
    range: str
    days: int
    points: List[ChartPoint]

class DashboardResponse(BaseModel):
    total_value: Decimal
    total_cost: Decimal
    total_pl: Decimal
    total_pl_percent: Decimal
    top_performer: Optional[Performer] = None
    worst_performer: Optional[Performer] = None
    holdings: List[HoldingWithMarket]
    market_data_available: bool = True

class CoinSearchResult(BaseModel):
    id: str
    symbol: str
    name: str
    thumb: Optional[str] = None
    large: Optional[str] = None
    market_cap_rank: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)
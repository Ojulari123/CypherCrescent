from fastapi import APIRouter, Depends, HTTPException, Query, status
from tables import User
from Schemas.marketSchema import *
from Utils.security import get_current_user
from typing import Optional
from Utils.coingecko import get_markets, get_top_markets, search_coins, get_market_chart, validate_coin_slug, MarketDataError

market_router = APIRouter()

RANGE_TO_DAYS = {
    ChartRange.DAY: 1,
    ChartRange.WEEK: 7,
    ChartRange.MONTH: 30,
}

# Get market data. Pass `ids` for specific coins (watchlist/holdings), or omit
# `ids` to page through the top coins by market cap (Markets page).
@market_router.get("/coins", response_model=list[CoinMarket], status_code=status.HTTP_200_OK)
def coin_markets(
    ids: Optional[str] = Query(None, description="Comma-separated CoinGecko ids (bitcoin,ethereum). Omit to list top coins by market cap."),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=250),
    current_user: User = Depends(get_current_user),
):
    try:
        if ids is not None:
            coin_ids = [s.strip().lower() for s in ids.split(",") if s.strip()]
            if not coin_ids:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Provide at least one coin id")
            data = get_markets(coin_ids)
        else:
            data = get_top_markets(page, per_page)
    except MarketDataError:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Market data unavailable")

    return [CoinMarket.model_validate(c) for c in data]

# Historical price chart for one coin
@market_router.get("/coins/{coin_id}/chart", response_model=ChartResponse, status_code=status.HTTP_200_OK)
def coin_chart(coin_id: str, range: ChartRange = Query(ChartRange.WEEK, description="Lookback window"), current_user: User = Depends(get_current_user)):
    coin_id = coin_id.strip().lower()
    if not coin_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Provide a coin id")

    validate_coin_slug(coin_id)

    days = RANGE_TO_DAYS[range]
    try:
        data = get_market_chart(coin_id, days)
    except MarketDataError:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Market data unavailable")

    points = [{"timestamp": int(ts), "price": price} for ts, price in data.get("prices", [])]
    return ChartResponse(coin_id=coin_id, range=range.value, days=days, points=points)

# Search coins by name or symbol
@market_router.get("/search", response_model=list[CoinSearchResult], status_code=status.HTTP_200_OK)
def search(q: str = Query(..., min_length=1, description="Search query"), current_user: User = Depends(get_current_user)):
    try:
        results = search_coins(q)
    except MarketDataError:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Search unavailable")

    return [CoinSearchResult.model_validate(c) for c in results]

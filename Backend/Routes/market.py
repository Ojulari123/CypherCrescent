import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status
from tables import *
from Schemas.marketSchema import *
from Utils.security import get_current_user
from Utils.coingecko import get_markets, search_coins

market_router = APIRouter()

# Get market data for one or more coins
@market_router.get("/coins", response_model=list[CoinMarket], status_code=status.HTTP_200_OK)
def coin_markets(ids: str = Query(..., description="Comma-separated CoinGecko ids, e.g. bitcoin,ethereum"), current_user: User = Depends(get_current_user)):
    coin_ids = [s.strip().lower() for s in ids.split(",") if s.strip()]
    if not coin_ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Provide at least one coin id")

    try:
        data = get_markets(coin_ids)
    except httpx.HTTPError:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Market data unavailable")

    return [CoinMarket.model_validate(c) for c in data]

# Search coins by name or symbol
@market_router.get("/search", response_model=list[CoinSearchResult], status_code=status.HTTP_200_OK)
def search(q: str = Query(..., min_length=1, description="Search query"), current_user: User = Depends(get_current_user)):
    try:
        results = search_coins(q)
    except httpx.HTTPError:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Search unavailable")

    return [CoinSearchResult.model_validate(c) for c in results]

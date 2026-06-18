import httpx
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from tables import get_db, User, Holding
from Schemas.marketSchema import DashboardResponse
from Utils.security import get_current_user
from Utils.coingecko import get_markets
from Utils.dashboard import build_dashboard

dashboard_router = APIRouter()

# Portfolio aggregate
@dashboard_router.get("", response_model=DashboardResponse, status_code=status.HTTP_200_OK)
def get_dashboard(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    holdings = db.query(Holding).filter(Holding.user_id == current_user.id).order_by(Holding.created_at.desc(), Holding.id.desc()).all()

    if not holdings:
        return DashboardResponse(
            total_value=0, total_cost=0, total_pl=0, total_pl_percent=0,
            top_performer=None, worst_performer=None, holdings=[],
            market_data_available=True,
        )

    coin_ids = [h.coin_slug for h in holdings]
    market_data_available = True
    try:
        market_data = get_markets(coin_ids)
    except httpx.HTTPError:
        market_data = []
        market_data_available = False

    result = build_dashboard(holdings, market_data, market_data_available)
    return DashboardResponse.model_validate(result)

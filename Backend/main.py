from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from Routes.user import user_router
from Routes.holding import holding_router
from Routes.market import market_router
from Routes.dashboard import dashboard_router
from Routes.watchlist import watchlist_router
from Utils.rate_limit import limiter

app = FastAPI(title="Cypher Crescent API")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://cypher-crescent.vercel.app",
                   "http://localhost:3000",
                   "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check
@app.get("/", tags=["Health"])
def health_check():
    return {"status": "ok"}

app.include_router(user_router, prefix="/api/users", tags=["Users"])
app.include_router(holding_router, prefix="/api/holdings", tags=["Holdings"])
app.include_router(market_router, prefix="/api/market", tags=["Market"])
app.include_router(dashboard_router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(watchlist_router, prefix="/api/watchlist", tags=["Watchlist"])

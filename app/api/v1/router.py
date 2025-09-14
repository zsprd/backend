from fastapi import APIRouter

from app.api.v1 import (
    accounts,
    analytics,
    auth,
    holdings,
    market_data,
    transactions,
    user,
)

api_router = APIRouter()

# Include all route modules
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(user.router, prefix="/users", tags=["users"])
api_router.include_router(accounts.router, prefix="/accounts", tags=["accounts"])
api_router.include_router(holdings.router, prefix="/accounts/holdings", tags=["holdings"])
api_router.include_router(
    transactions.router, prefix="/accounts/transactions", tags=["transactions"]
)
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(market_data.router, prefix="/market-data", tags=["market-data"])

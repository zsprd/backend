from fastapi import APIRouter

from app.api.v1 import auth, users, accounts, holdings, transactions, analytics, market_data

api_router = APIRouter()

# Include all route modules
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(accounts.router, prefix="/accounts", tags=["accounts"])
api_router.include_router(holdings.router, prefix="/holdings", tags=["holdings"])
api_router.include_router(transactions.router, prefix="/transactions", tags=["transactions"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(market_data.router, prefix="/market-data", tags=["market-data"])
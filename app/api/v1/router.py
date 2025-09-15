from fastapi import APIRouter

from app.auth.router import router as auth
from app.users.profile.router import router as user

api_router = APIRouter()

# Include all route modules
api_router.include_router(auth, prefix="/auth", tags=["Authentication"])
api_router.include_router(user, prefix="/users", tags=["User"])
# api_router.include_router(account.router, prefix="/portfolios/accounts", tags=["Portfolio"])
# api_router.include_router(holding.router, prefix="/portfolios/holdings", tags=["Portfolio"])
# api_router.include_router(transaction.router, prefix="/portfolios/transactions", tags=["Portfolio"])
# api_router.include_router(exposure.router, prefix="/analytics/exposure", tags=["Analytics"])
# api_router.include_router(performance.router, prefix="/analytics/performance", tags=["Analytics"])
# api_router.include_router(risk.router, prefix="/analytics/risk", tags=["Analytics"])
# api_router.include_router(summary.router, prefix="/analytics/summary", tags=["Analytics"])
# api_router.include_router(security.router, prefix="/security", tags=["Security"])

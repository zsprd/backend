from fastapi import APIRouter

# import app.analytics.exposure.router as exposure
# import app.analytics.performance.router as performance
# import app.analytics.risk.router as risk
# import app.analytics.summary.router as summary
import app.auth.router as auth
import app.portfolio.accounts.router as account

# import app.portfolio.holdings.router as holding
# import app.portfolio.transactions.router as transaction
# import app.security.master.router as security
import app.user.accounts.router as user

api_router = APIRouter()

# Include all route modules
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(user.router, prefix="/user", tags=["User"])
api_router.include_router(account.router, prefix="/portfolios/accounts", tags=["Portfolio"])
# api_router.include_router(holding.router, prefix="/portfolios/holdings", tags=["Portfolio"])
# api_router.include_router(transaction.router, prefix="/portfolios/transactions", tags=["Portfolio"])
# api_router.include_router(exposure.router, prefix="/analytics/exposure", tags=["Analytics"])
# api_router.include_router(performance.router, prefix="/analytics/performance", tags=["Analytics"])
# api_router.include_router(risk.router, prefix="/analytics/risk", tags=["Analytics"])
# api_router.include_router(summary.router, prefix="/analytics/summary", tags=["Analytics"])
# api_router.include_router(security.router, prefix="/security", tags=["Security"])

# import app.security.master.router as security
from fastapi import APIRouter

import app.account.holdings.router as holding
import app.account.master.router as account
# import app.analytics.exposure.router as exposure
# import app.analytics.performance.router as performance
# import app.analytics.risk.router as risk
# import app.analytics.summary.router as summary
import app.auth.router as auth
import app.integrations.csv.router as csv_import
import app.user.master.router as user

# import app.account.transactions.router as transaction

api_router = APIRouter()

# Include all route modules
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(user.router, prefix="/user", tags=["User"])
api_router.include_router(account.router, prefix="/account", tags=["Portfolio"])
api_router.include_router(holding.router, prefix="/account/holdings", tags=["Portfolio"])
# api_router.include_router(transaction.router, prefix="/account/transactions", tags=["Portfolio"])
api_router.include_router(csv_import.router, prefix="/data/csv", tags=["CSV Import"])
# api_router.include_router(exposure.router, prefix="/analytics/exposure", tags=["Analytics"])
# api_router.include_router(performance.router, prefix="/analytics/performance", tags=["Analytics"])
# api_router.include_router(risk.router, prefix="/analytics/risk", tags=["Analytics"])
# api_router.include_router(summary.router, prefix="/analytics/summary", tags=["Analytics"])
# api_router.include_router(security.router, prefix="/security", tags=["Security"])

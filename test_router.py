
from fastapi import APIRouter

router = APIRouter()

@router.get("/test")
async def test_endpoint():
    return {"message": "Test endpoint working"}

@router.get("/accounts")
async def test_accounts():
    return {"accounts": [], "message": "Minimal accounts endpoint"}

@router.get("/analytics/performance")
async def test_performance():
    return {"total_return": 0.0, "message": "Minimal performance endpoint"}

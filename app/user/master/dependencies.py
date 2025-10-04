import logging

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.user.master.service import UserService

logger = logging.getLogger(__name__)


def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    """Dependency injection for user service."""
    return UserService(db)

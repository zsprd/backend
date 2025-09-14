"""
CRUD module initialization and registry.
Import all CRUD instances and create a factory for type-safe access.
"""

from typing import Any, Dict, Optional, Type, TypeVar

from app.crud.account import account_crud
from app.crud.audit_log import audit_log_crud
from app.crud.holding import holding_crud
from app.crud.security import security_crud  # Your existing securities CRUD
from app.crud.transaction import transaction_crud

# Import all CRUD instances
from app.crud.user import user_crud
from app.crud.user_session import user_session_crud
from app.models.monitoring.audit import AuditLog
from app.models.portfolios.account import PortfolioAccount
from app.models.portfolios.holding import PortfolioHolding
from app.models.portfolios.transaction import PortfolioTransaction
from app.models.securities.reference import SecurityReference
from app.models.users.session import UserSession

# Import models for type checking
from app.models.users.user import User

T = TypeVar("T")


class CRUDFactory:
    """Factory for creating CRUD instances with proper typing."""

    _crud_registry: Dict[Type, Any] = {}

    @classmethod
    def register_crud(cls, model_class: Type, crud_instance: Any) -> None:
        """Register a CRUD instance for a model."""
        cls._crud_registry[model_class] = crud_instance

    @classmethod
    def get_crud(cls, model_class: Type[T]) -> Optional[Any]:
        """Get CRUD instance for a model."""
        return cls._crud_registry.get(model_class)

    @classmethod
    def register_all_crud(cls) -> None:
        """Register all CRUD instances."""
        cls.register_crud(User, user_crud)
        cls.register_crud(UserSession, user_session_crud)
        cls.register_crud(PortfolioAccount, account_crud)
        cls.register_crud(PortfolioHolding, holding_crud)
        cls.register_crud(PortfolioTransaction, transaction_crud)
        cls.register_crud(AuditLog, audit_log_crud)
        cls.register_crud(SecurityReference, security_crud)

    @classmethod
    def list_registered_models(cls) -> list:
        """List all registered model classes."""
        return list(cls._crud_registry.keys())


# Initialize the registry
CRUDFactory.register_all_crud()

# Export all CRUD instances for direct import
__all__ = [
    "user_crud",
    "user_session_crud",
    "account_crud",
    "holding_crud",
    "transaction_crud",
    "audit_log_crud",
    "security_crud",
    "CRUDFactory",
]


# Convenience functions for common operations
def get_user_crud():
    """Get users CRUD instance."""
    return user_crud


def get_account_crud():
    """Get account CRUD instance."""
    return account_crud


def get_audit_crud():
    """Get audit log CRUD instance."""
    return audit_log_crud


# Export convenience functions
__all__.extend(["get_user_crud", "get_account_crud", "get_audit_crud"])

"""
CRUD module initialization and registry.
Import all CRUD instances and create a factory for type-safe access.
"""

from typing import Any, Dict, Optional, Type, TypeVar

from app.crud.account import account_crud
from app.crud.audit_log import audit_log_crud
from app.crud.holding import holding_crud
from app.crud.security import security_crud  # Your existing security CRUD
from app.crud.transaction import transaction_crud

# Import all CRUD instances
from app.crud.user import user_crud
from app.crud.user_session import user_session_crud
from app.models.core.account import Account

# Import models for type checking
from app.models.core.user import User
from app.models.holding import Holding
from app.models.security.security import Security
from app.models.system.audit_log import AuditLog
from app.models.system.user_session import UserSession
from app.models.transaction import Transaction

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
        cls.register_crud(Account, account_crud)
        cls.register_crud(Holding, holding_crud)
        cls.register_crud(Transaction, transaction_crud)
        cls.register_crud(AuditLog, audit_log_crud)
        cls.register_crud(Security, security_crud)

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
    """Get user CRUD instance."""
    return user_crud


def get_account_crud():
    """Get account CRUD instance."""
    return account_crud


def get_audit_crud():
    """Get audit log CRUD instance."""
    return audit_log_crud


# Export convenience functions
__all__.extend(["get_user_crud", "get_account_crud", "get_audit_crud"])

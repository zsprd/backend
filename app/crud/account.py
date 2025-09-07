from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_

from app.crud.base import CRUDBase
from app.models.account import Account, Institution


class CRUDAccount(CRUDBase[Account, dict, dict]):
    def get_multi_by_user(
        self,
        db: Session,
        *,
        user_id: str,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Account]:
        """Get multiple accounts for a specific user with optional filters."""
        query = db.query(Account).options(joinedload(Account.institution)).filter(
            Account.user_id == user_id
        )
        
        # Apply additional filters
        if filters:
            for key, value in filters.items():
                if hasattr(Account, key) and value is not None:
                    query = query.filter(getattr(Account, key) == value)
        
        return query.offset(skip).limit(limit).all()

    def get_by_user_and_id(
        self, 
        db: Session, 
        *, 
        user_id: str, 
        account_id: str
    ) -> Optional[Account]:
        """Get a specific account for a user."""
        return db.query(Account).options(joinedload(Account.institution)).filter(
            and_(Account.id == account_id, Account.user_id == user_id)
        ).first()

    def get_active_accounts_by_user(
        self,
        db: Session,
        *,
        user_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Account]:
        """Get all active accounts for a user."""
        return db.query(Account).options(joinedload(Account.institution)).filter(
            and_(Account.user_id == user_id, Account.is_active == True)
        ).offset(skip).limit(limit).all()

    def count_by_user(self, db: Session, *, user_id: str) -> int:
        """Count total accounts for a user."""
        return db.query(Account).filter(Account.user_id == user_id).count()

    def count_active_by_user(self, db: Session, *, user_id: str) -> int:
        """Count active accounts for a user."""
        return db.query(Account).filter(
            and_(Account.user_id == user_id, Account.is_active == True)
        ).count()

    def get_by_plaid_account_id(
        self, 
        db: Session, 
        *, 
        plaid_account_id: str
    ) -> Optional[Account]:
        """Get account by Plaid account ID."""
        return db.query(Account).filter(
            Account.plaid_account_id == plaid_account_id
        ).first()

    def soft_delete(self, db: Session, *, account_id: str, user_id: str) -> Optional[Account]:
        """Soft delete an account by setting is_active to False."""
        account = self.get_by_user_and_id(db, user_id=user_id, account_id=account_id)
        if account:
            account.is_active = False
            db.add(account)
            db.commit()
            db.refresh(account)
        return account

    def get_accounts_by_type(
        self,
        db: Session,
        *,
        user_id: str,
        account_type: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Account]:
        """Get accounts by type for a user."""
        return db.query(Account).options(joinedload(Account.institution)).filter(
            and_(
                Account.user_id == user_id, 
                Account.type == account_type,
                Account.is_active == True
            )
        ).offset(skip).limit(limit).all()


class CRUDInstitution(CRUDBase[Institution, dict, dict]):
    def get_by_plaid_id(
        self, 
        db: Session, 
        *, 
        plaid_institution_id: str
    ) -> Optional[Institution]:
        """Get institution by Plaid institution ID."""
        return db.query(Institution).filter(
            Institution.plaid_institution_id == plaid_institution_id
        ).first()

    def get_by_name(self, db: Session, *, name: str) -> Optional[Institution]:
        """Get institution by name."""
        return db.query(Institution).filter(Institution.name == name).first()

    def search_by_name(
        self, 
        db: Session, 
        *, 
        name_pattern: str, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[Institution]:
        """Search institutions by name pattern."""
        return db.query(Institution).filter(
            Institution.name.ilike(f"%{name_pattern}%")
        ).offset(skip).limit(limit).all()


# Create instances
account_crud = CRUDAccount(Account)
institution_crud = CRUDInstitution(Institution)
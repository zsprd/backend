from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import select, and_
from datetime import datetime, timezone

from app.crud.base import CRUDBase
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.core.auth import hash_password, verify_password


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    """CRUD operations for User model with proper typing."""

    def get_by_email(self, db: Session, *, email: str) -> Optional[User]:
        """Get user by email address using SQLAlchemy 2.0 syntax."""
        stmt = select(User).where(User.email == email)
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def get_by_google_id(self, db: Session, *, google_id: str) -> Optional[User]:
        """Get user by Google ID using SQLAlchemy 2.0 syntax."""
        stmt = select(User).where(User.google_id == google_id)
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def get_by_apple_id(self, db: Session, *, apple_id: str) -> Optional[User]:
        """Get user by Apple ID using SQLAlchemy 2.0 syntax."""
        stmt = select(User).where(User.apple_id == apple_id)
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def get_active_users(
        self, 
        db: Session, 
        *, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[User]:
        """Get active users with pagination."""
        stmt = select(User).where(User.is_active == True).offset(skip).limit(limit)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def create_user(
        self,
        db: Session,
        *,
        email: str,
        password: Optional[str] = None,
        full_name: Optional[str] = None,
        google_id: Optional[str] = None,
        apple_id: Optional[str] = None,
        base_currency: str = "USD",
        timezone: str = "UTC",
        is_verified: bool = False
    ) -> User:
        """Create new user with secure password hashing."""
        user_data = {
            "email": email,
            "full_name": full_name,
            "base_currency": base_currency.upper(),
            "timezone": timezone,
            "google_id": google_id,
            "apple_id": apple_id,
            "is_active": True,
            "is_verified": is_verified,
            "is_premium": False,
            "language": "en",
            "theme_preference": "system"
        }
        
        # Hash password if provided
        if password:
            user_data["password_hash"] = hash_password(password)
        
        user = User(**user_data)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    def authenticate_user(
        self, 
        db: Session, 
        *, 
        email: str, 
        password: str
    ) -> Optional[User]:
        """Authenticate user with email and password."""
        user = self.get_by_email(db, email=email)
        
        if not user or not user.password_hash:
            return None
        
        if not verify_password(password, user.password_hash):
            return None
        
        if not user.is_active:
            return None
        
        return user

    def update_password(
        self, 
        db: Session, 
        *, 
        user: User, 
        new_password: str
    ) -> User:
        """Update user password with secure hashing."""
        user.password_hash = hash_password(new_password)
        user.updated_at = datetime.now(timezone.utc)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    def verify_email(self, db: Session, *, user_id: str) -> Optional[User]:
        """Mark user email as verified."""
        user = self.get(db, id=user_id)
        if user:
            user.is_verified = True
            user.updated_at = datetime.now(timezone.utc)
            db.add(user)
            db.commit()
            db.refresh(user)
        return user

    def update_last_login(self, db: Session, *, user: User) -> User:
        """Update user's last login timestamp."""
        user.last_login_at = datetime.now(timezone.utc)
        user.updated_at = datetime.now(timezone.utc)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    def update_profile(
        self, 
        db: Session, 
        *, 
        user: User, 
        update_data: dict
    ) -> User:
        """Update user profile with safe fields only."""
        allowed_fields = {
            'full_name', 'base_currency', 'timezone', 
            'language', 'theme_preference'
        }
        
        for field, value in update_data.items():
            if field in allowed_fields and hasattr(user, field):
                if field == 'base_currency' and value:
                    setattr(user, field, value.upper())
                elif field == 'language' and value:
                    setattr(user, field, value.lower())
                else:
                    setattr(user, field, value)
        
        user.updated_at = datetime.now(timezone.utc)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    def deactivate_user(self, db: Session, *, user_id: str) -> Optional[User]:
        """Soft delete user by setting is_active to False."""
        user = self.get(db, id=user_id)
        if user:
            user.is_active = False
            user.updated_at = datetime.now(timezone.utc)
            db.add(user)
            db.commit()
            db.refresh(user)
        return user

    def count_by_status(
        self, 
        db: Session, 
        *, 
        is_active: Optional[bool] = None,
        is_verified: Optional[bool] = None
    ) -> int:
        """Count users by status filters."""
        filters = {}
        if is_active is not None:
            filters['is_active'] = is_active
        if is_verified is not None:
            filters['is_verified'] = is_verified
        
        return self.count(db, filters=filters)

    def get_user_stats(self, db: Session) -> dict:
        """Get comprehensive user statistics."""
        total_users = self.count(db)
        active_users = self.count_by_status(db, is_active=True)
        verified_users = self.count_by_status(db, is_verified=True)
        premium_users = self.count(db, filters={'is_premium': True})
        
        return {
            "total_users": total_users,
            "active_users": active_users,
            "inactive_users": total_users - active_users,
            "verified_users": verified_users,
            "unverified_users": total_users - verified_users,
            "premium_users": premium_users,
            "free_users": total_users - premium_users,
            "verification_rate": round((verified_users / total_users * 100), 2) if total_users > 0 else 0,
            "premium_conversion_rate": round((premium_users / total_users * 100), 2) if total_users > 0 else 0
        }


# Create instance
user_crud = CRUDUser(User)

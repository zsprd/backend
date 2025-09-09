from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime, timezone

from app.crud.base import CRUDBase
from app.models.user import User
from app.core.auth import hash_password, verify_password


class CRUDUser(CRUDBase[User, None, None]):
    """CRUD operations for User model."""

    def get_by_email(self, db: Session, *, email: str) -> Optional[User]:
        """Get user by email address."""
        return db.query(User).filter(User.email == email).first()

    def get_by_google_id(self, db: Session, *, google_id: str) -> Optional[User]:
        """Get user by Google ID."""
        return db.query(User).filter(User.google_id == google_id).first()

    def get_by_apple_id(self, db: Session, *, apple_id: str) -> Optional[User]:
        """Get user by Apple ID."""
        return db.query(User).filter(User.apple_id == apple_id).first()

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
            "base_currency": base_currency,
            "timezone": timezone,
            "google_id": google_id,
            "apple_id": apple_id,
            "is_active": True,
            "is_verified": is_verified,
            "is_premium": False
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
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    def verify_email(self, db: Session, *, user_id: str) -> User:
        """Mark user email as verified."""
        user = self.get(db, id=user_id)
        user.is_verified = True
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    def update_last_login(self, db: Session, *, user: User) -> User:
        """Update user's last login timestamp."""
        user.last_login_at = datetime.now(timezone.utc)
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
                setattr(user, field, value)
        
        db.add(user)
        db.commit()
        db.refresh(user)
        return user


user_crud = CRUDUser(User)

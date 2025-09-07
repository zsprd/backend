from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.crud.base import CRUDBase
from app.models.user import User


class CRUDUser(CRUDBase[User, None, None]):
    def get_by_email(self, db: Session, *, email: str) -> Optional[User]:
        """Get user by email address."""
        return db.query(User).filter(User.email == email).first()

    def get_by_google_id(self, db: Session, *, google_id: str) -> Optional[User]:
        """Get user by Google OAuth ID."""
        return db.query(User).filter(User.google_id == google_id).first()

    def get_by_apple_id(self, db: Session, *, apple_id: str) -> Optional[User]:
        """Get user by Apple OAuth ID."""
        return db.query(User).filter(User.apple_id == apple_id).first()

    def get_by_oauth_id(
        self, 
        db: Session, 
        *, 
        provider: str, 
        oauth_id: str
    ) -> Optional[User]:
        """Get user by OAuth provider and ID."""
        if provider == "google":
            return self.get_by_google_id(db, google_id=oauth_id)
        elif provider == "apple":
            return self.get_by_apple_id(db, apple_id=oauth_id)
        return None

    def create_user(
        self, 
        db: Session, 
        *, 
        email: str,
        full_name: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        oauth_provider: Optional[str] = None,
        oauth_id: Optional[str] = None,
        **kwargs
    ) -> User:
        """Create a new user with OAuth or email registration."""
        user_data = {
            "email": email,
            "full_name": full_name,
            "first_name": first_name,
            "last_name": last_name,
            "email_verified": True if oauth_provider else False,
            "is_active": True,
            **kwargs
        }
        
        # Set OAuth ID based on provider
        if oauth_provider == "google":
            user_data["google_id"] = oauth_id
        elif oauth_provider == "apple":
            user_data["apple_id"] = oauth_id
        
        return self.create_from_dict(db, obj_in=user_data)

    def update_last_login(self, db: Session, *, user: User) -> User:
        """Update user's last login timestamp."""
        from datetime import datetime
        user.last_login_at = datetime.utcnow()
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    def activate_user(self, db: Session, *, user_id: str) -> Optional[User]:
        """Activate a user account."""
        user = self.get(db, id=user_id)
        if user:
            user.is_active = True
            db.add(user)
            db.commit()
            db.refresh(user)
        return user

    def deactivate_user(self, db: Session, *, user_id: str) -> Optional[User]:
        """Deactivate a user account."""
        user = self.get(db, id=user_id)
        if user:
            user.is_active = False
            db.add(user)
            db.commit()
            db.refresh(user)
        return user

    def verify_email(self, db: Session, *, user_id: str) -> Optional[User]:
        """Mark user's email as verified."""
        user = self.get(db, id=user_id)
        if user:
            user.email_verified = True
            user.is_verified = True
            db.add(user)
            db.commit()
            db.refresh(user)
        return user

    def search_users(
        self, 
        db: Session, 
        *, 
        search_term: str, 
        skip: int = 0, 
        limit: int = 100
    ) -> list[User]:
        """Search users by email or name."""
        return db.query(User).filter(
            or_(
                User.email.ilike(f"%{search_term}%"),
                User.full_name.ilike(f"%{search_term}%"),
                User.first_name.ilike(f"%{search_term}%"),
                User.last_name.ilike(f"%{search_term}%")
            )
        ).offset(skip).limit(limit).all()

    def count_active_users(self, db: Session) -> int:
        """Count total active users."""
        return db.query(User).filter(User.is_active == True).count()

    def count_verified_users(self, db: Session) -> int:
        """Count total verified users."""
        return db.query(User).filter(User.is_verified == True).count()


# Create instance
user_crud = CRUDUser(User)
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from app.crud.base import CRUDBase
from app.models.user import User


class CRUDUser(CRUDBase[User, None, None]):
    """
    CRUD operations for User model with enhanced authentication features.
    """
    
    def get_by_email(self, db: Session, *, email: str) -> Optional[User]:
        """Get user by email address."""
        return db.query(User).filter(User.email == email.lower()).first()

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
        password_hash: Optional[str] = None,
        full_name: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        oauth_provider: Optional[str] = None,
        oauth_id: Optional[str] = None,
        is_active: bool = True,
        is_verified: bool = False,
        **kwargs
    ) -> User:
        """
        Create a new user with various registration methods.
        
        Args:
            email: User's email address
            password_hash: Already hashed password from frontend
            full_name: User's full name
            first_name: User's first name
            last_name: User's last name
            oauth_provider: OAuth provider (google, apple)
            oauth_id: OAuth provider's user ID
            is_active: Whether user account is active
            is_verified: Whether email is verified
            **kwargs: Additional user fields
        """
        # Prepare user data
        user_data = {
            "email": email.lower(),
            "password_hash": password_hash,
            "full_name": full_name,
            "first_name": first_name,
            "last_name": last_name,
            "is_active": is_active,
            "is_verified": is_verified,
            "email_verified": is_verified,  # Keep both fields in sync
            **kwargs
        }
        
        # Set OAuth ID based on provider
        if oauth_provider == "google":
            user_data["google_id"] = oauth_id
            user_data["email_verified"] = True
            user_data["is_verified"] = True
        elif oauth_provider == "apple":
            user_data["apple_id"] = oauth_id
            user_data["email_verified"] = True
            user_data["is_verified"] = True
        
        # Remove None values
        user_data = {k: v for k, v in user_data.items() if v is not None}
        
        # Create user
        db_user = User(**user_data)
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

    def update_user(
        self, 
        db: Session, 
        *, 
        user: User, 
        update_data: Dict[str, Any]
    ) -> User:
        """
        Update user with provided data.
        """
        for field, value in update_data.items():
            if hasattr(user, field) and value is not None:
                setattr(user, field, value)
        
        user.updated_at = datetime.utcnow()
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    def update_password(
        self, 
        db: Session, 
        *, 
        user: User, 
        new_password_hash: str
    ) -> User:
        """
        Update user's password hash.
        
        Args:
            user: User object
            new_password_hash: New password hash from frontend
        """
        user.password_hash = new_password_hash
        user.updated_at = datetime.utcnow()
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    def update_last_login(self, db: Session, *, user: User) -> User:
        """Update user's last login timestamp."""
        user.last_login_at = datetime.utcnow()
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    def verify_email(self, db: Session, *, user_id: str) -> Optional[User]:
        """
        Mark user's email as verified.
        Updates both email_verified and is_verified fields.
        """
        user = self.get(db, id=user_id)
        if user:
            user.email_verified = True
            user.is_verified = True
            user.updated_at = datetime.utcnow()
            db.add(user)
            db.commit()
            db.refresh(user)
        return user

    def activate_user(self, db: Session, *, user_id: str) -> Optional[User]:
        """Activate a user account."""
        user = self.get(db, id=user_id)
        if user:
            user.is_active = True
            user.updated_at = datetime.utcnow()
            db.add(user)
            db.commit()
            db.refresh(user)
        return user

    def deactivate_user(self, db: Session, *, user_id: str) -> Optional[User]:
        """Deactivate a user account."""
        user = self.get(db, id=user_id)
        if user:
            user.is_active = False
            user.updated_at = datetime.utcnow()
            db.add(user)
            db.commit()
            db.refresh(user)
        return user

    def soft_delete_user(self, db: Session, *, user_id: str) -> Optional[User]:
        """
        Soft delete a user (deactivate and anonymize).
        """
        user = self.get(db, id=user_id)
        if user:
            user.is_active = False
            user.email = f"deleted_{user.id}@deleted.com"
            user.full_name = "Deleted User"
            user.first_name = None
            user.last_name = None
            user.password_hash = None
            user.updated_at = datetime.utcnow()
            db.add(user)
            db.commit()
            db.refresh(user)
        return user

    def update_profile(
        self,
        db: Session,
        *,
        user: User,
        full_name: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        base_currency: Optional[str] = None,
        theme_preference: Optional[str] = None,
        timezone: Optional[str] = None,
        language: Optional[str] = None
    ) -> User:
        """Update user profile information."""
        update_data = {}
        
        if full_name is not None:
            update_data["full_name"] = full_name
        if first_name is not None:
            update_data["first_name"] = first_name
        if last_name is not None:
            update_data["last_name"] = last_name
        if base_currency is not None:
            update_data["base_currency"] = base_currency
        if theme_preference is not None:
            update_data["theme_preference"] = theme_preference
        if timezone is not None:
            update_data["timezone"] = timezone
        if language is not None:
            update_data["language"] = language
        
        return self.update_user(db, user=user, update_data=update_data)

    def update_premium_status(
        self, 
        db: Session, 
        *, 
        user_id: str, 
        is_premium: bool
    ) -> Optional[User]:
        """Update user's premium status."""
        user = self.get(db, id=user_id)
        if user:
            user.is_premium = is_premium
            user.updated_at = datetime.utcnow()
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
        limit: int = 100,
        active_only: bool = True
    ) -> list[User]:
        """
        Search users by email or name.
        
        Args:
            search_term: Term to search for
            skip: Number of records to skip
            limit: Maximum number of records to return
            active_only: Only return active users
        """
        query = db.query(User).filter(
            or_(
                User.email.ilike(f"%{search_term}%"),
                User.full_name.ilike(f"%{search_term}%"),
                User.first_name.ilike(f"%{search_term}%"),
                User.last_name.ilike(f"%{search_term}%")
            )
        )
        
        if active_only:
            query = query.filter(User.is_active == True)
        
        return query.offset(skip).limit(limit).all()

    def get_users_by_status(
        self,
        db: Session,
        *,
        is_active: Optional[bool] = None,
        is_verified: Optional[bool] = None,
        is_premium: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> list[User]:
        """Get users filtered by various status flags."""
        query = db.query(User)
        
        if is_active is not None:
            query = query.filter(User.is_active == is_active)
        if is_verified is not None:
            query = query.filter(User.is_verified == is_verified)
        if is_premium is not None:
            query = query.filter(User.is_premium == is_premium)
        
        return query.offset(skip).limit(limit).all()

    def count_users_by_status(self, db: Session) -> Dict[str, int]:
        """Get count of users by various status categories."""
        total = db.query(User).count()
        active = db.query(User).filter(User.is_active == True).count()
        verified = db.query(User).filter(User.is_verified == True).count()
        premium = db.query(User).filter(User.is_premium == True).count()
        unverified = db.query(User).filter(
            and_(User.is_active == True, User.is_verified == False)
        ).count()
        
        return {
            "total": total,
            "active": active,
            "verified": verified,
            "premium": premium,
            "unverified": unverified,
            "inactive": total - active
        }

    def get_recent_signups(
        self, 
        db: Session, 
        *, 
        days: int = 30, 
        limit: int = 100
    ) -> list[User]:
        """Get users who signed up in the last N days."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        return db.query(User).filter(
            User.created_at >= cutoff_date
        ).order_by(User.created_at.desc()).limit(limit).all()

    def get_users_never_logged_in(
        self, 
        db: Session, 
        *, 
        days_since_signup: int = 7,
        limit: int = 100
    ) -> list[User]:
        """Get users who never logged in after N days of signup."""
        cutoff_date = datetime.utcnow() - timedelta(days=days_since_signup)
        return db.query(User).filter(
            and_(
                User.created_at <= cutoff_date,
                User.last_login_at.is_(None),
                User.is_active == True
            )
        ).order_by(User.created_at.desc()).limit(limit).all()

    def bulk_update_users(
        self,
        db: Session,
        *,
        user_ids: list[str],
        update_data: Dict[str, Any]
    ) -> int:
        """
        Bulk update multiple users.
        Returns the number of updated records.
        """
        update_data["updated_at"] = datetime.utcnow()
        
        result = db.query(User).filter(
            User.id.in_(user_ids)
        ).update(update_data, synchronize_session=False)
        
        db.commit()
        return result

    def email_exists(self, db: Session, *, email: str) -> bool:
        """Check if email already exists in the database."""
        return db.query(User).filter(User.email == email.lower()).first() is not None

    def get_user_stats(self, db: Session, *, user_id: str) -> Dict[str, Any]:
        """
        Get comprehensive user statistics.
        This will be extended when other models are available.
        """
        user = self.get(db, id=user_id)
        if not user:
            return {}
        
        # Basic user stats (extend when you have accounts, transactions, etc.)
        return {
            "user_id": str(user.id),
            "member_since": user.created_at.isoformat(),
            "last_login": user.last_login_at.isoformat() if user.last_login_at else None,
            "is_verified": user.is_verified,
            "is_premium": user.is_premium,
            "days_since_signup": (datetime.utcnow() - user.created_at).days,
            "total_logins": 0,  # Implement when you have login tracking
            "total_accounts": 0,  # Implement when you have accounts table
            "total_transactions": 0,  # Implement when you have transactions table
            "portfolio_value": 0.0,  # Implement when you have holdings/positions
        }


# Create instance
user_crud = CRUDUser(User)
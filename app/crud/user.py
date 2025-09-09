from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from app.crud.base import CRUDBase
from app.models.user import User
from app.core.password import hash_password, verify_password  # Import from password module


class CRUDUser(CRUDBase[User, None, None]):
    """
    CRUD operations for User model with secure password handling.
    All passwords are hashed using bcrypt with salt.
    """
    
    def get_by_email(self, db: Session, *, email: str) -> Optional[User]:
        """Get user by email address (case-insensitive)."""
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
        password: Optional[str] = None,  # Plain password - will be hashed
        full_name: Optional[str] = None,
        oauth_provider: Optional[str] = None,
        oauth_id: Optional[str] = None,
        is_active: bool = True,
        is_verified: bool = False,
        **kwargs
    ) -> User:
        """
        Create a new user with secure password hashing.
        
        Args:
            email: User's email address
            password: Plain password (will be hashed with bcrypt)
            full_name: User's full name
            oauth_provider: OAuth provider (google, apple)
            oauth_id: OAuth provider's user ID
            is_active: Whether user account is active
            is_verified: Whether email is verified
            **kwargs: Additional user fields
            
        Returns:
            Created User object
        """
        # Prepare user data
        user_data = {
            "email": email.lower(),
            "full_name": full_name,
            "is_active": is_active,
            "is_verified": is_verified,
            **kwargs
        }
        
        # Hash password if provided
        if password:
            user_data["password_hash"] = hash_password(password)
        
        # Set OAuth fields and auto-verify OAuth users
        if oauth_provider == "google":
            user_data["google_id"] = oauth_id
            user_data["is_verified"] = True  # OAuth users are pre-verified
        elif oauth_provider == "apple":
            user_data["apple_id"] = oauth_id
            user_data["is_verified"] = True  # OAuth users are pre-verified
        
        # Remove None values to use database defaults
        user_data = {k: v for k, v in user_data.items() if v is not None}
        
        # Create and save user
        db_user = User(**user_data)
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

    def authenticate_user(
        self, 
        db: Session, 
        *, 
        email: str, 
        password: str
    ) -> Optional[User]:
        """
        Authenticate user with email and password.
        
        Args:
            email: User's email address
            password: Plain password to verify
            
        Returns:
            User object if authentication successful, None otherwise
        """
        user = self.get_by_email(db, email=email)
        
        if not user:
            # Always hash password even for non-existent users 
            # to prevent timing attacks
            hash_password("dummy_password")
            return None
        
        if not user.password_hash:
            return None  # User has no password (OAuth only)
        
        if not verify_password(password, user.password_hash):
            return None
        
        if not user.is_active:
            return None  # Account is disabled
        
        return user

    def update_user(
        self, 
        db: Session, 
        *, 
        user: User, 
        update_data: Dict[str, Any]
    ) -> User:
        """
        Update user with provided data.
        Automatically updates the updated_at timestamp.
        """
        # Don't allow direct password_hash updates through this method
        if "password_hash" in update_data:
            update_data.pop("password_hash")
        
        # Update fields
        for field, value in update_data.items():
            if hasattr(user, field) and value is not None:
                setattr(user, field, value)
        
        # Auto-update timestamp
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
        new_password: str
    ) -> User:
        """
        Update user's password with secure hashing.
        
        Args:
            user: User object
            new_password: Plain new password (will be hashed)
        """
        user.password_hash = hash_password(new_password)
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
        
        Args:
            user_id: User's UUID as string
            
        Returns:
            Updated User object or None if not found
        """
        user = self.get(db, id=user_id)
        if user:
            user.is_verified = True
            user.updated_at = datetime.utcnow()
            db.add(user)
            db.commit()
            db.refresh(user)
        return user

    def deactivate_user(self, db: Session, *, user_id: str) -> Optional[User]:
        """
        Deactivate user account (soft delete).
        """
        user = self.get(db, id=user_id)
        if user:
            user.is_active = False
            user.updated_at = datetime.utcnow()
            db.add(user)
            db.commit()
            db.refresh(user)
        return user

    def reactivate_user(self, db: Session, *, user_id: str) -> Optional[User]:
        """
        Reactivate user account.
        """
        user = self.get(db, id=user_id)
        if user:
            user.is_active = True
            user.updated_at = datetime.utcnow()
            db.add(user)
            db.commit()
            db.refresh(user)
        return user

    def get_users_by_status(
        self,
        db: Session,
        *,
        is_active: Optional[bool] = None,
        is_verified: Optional[bool] = None,
        is_premium: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[User]:
        """
        Get users filtered by status flags.
        """
        query = db.query(User)
        
        if is_active is not None:
            query = query.filter(User.is_active == is_active)
        if is_verified is not None:
            query = query.filter(User.is_verified == is_verified)
        if is_premium is not None:
            query = query.filter(User.is_premium == is_premium)
        
        return query.offset(offset).limit(limit).all()

    def search_users(
        self,
        db: Session,
        *,
        search_term: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[User]:
        """
        Search users by email or full_name.
        """
        search_pattern = f"%{search_term.lower()}%"
        
        return db.query(User).filter(
            or_(
                User.email.ilike(search_pattern),
                User.full_name.ilike(search_pattern)
            )
        ).filter(
            User.is_active == True  # Only search active users
        ).offset(offset).limit(limit).all()

    def get_users_created_after(
        self,
        db: Session,
        *,
        created_after: datetime,
        limit: int = 100,
        offset: int = 0
    ) -> List[User]:
        """
        Get users created after a specific date.
        Useful for analytics and reporting.
        """
        return db.query(User).filter(
            User.created_at >= created_after
        ).order_by(
            User.created_at.desc()
        ).offset(offset).limit(limit).all()

    def count_users_by_status(
        self,
        db: Session
    ) -> Dict[str, int]:
        """
        Get user counts by various status flags.
        Useful for admin dashboard metrics.
        """
        total_users = db.query(User).count()
        active_users = db.query(User).filter(User.is_active == True).count()
        verified_users = db.query(User).filter(User.is_verified == True).count()
        premium_users = db.query(User).filter(User.is_premium == True).count()
        oauth_users = db.query(User).filter(
            or_(User.google_id.isnot(None), User.apple_id.isnot(None))
        ).count()
        
        return {
            "total": total_users,
            "active": active_users,
            "verified": verified_users,
            "premium": premium_users,
            "oauth": oauth_users,
            "inactive": total_users - active_users,
            "unverified": total_users - verified_users
        }

    def link_oauth_account(
        self,
        db: Session,
        *,
        user: User,
        provider: str,
        oauth_id: str
    ) -> User:
        """
        Link OAuth account to existing user.
        """
        if provider == "google":
            user.google_id = oauth_id
        elif provider == "apple":
            user.apple_id = oauth_id
        else:
            raise ValueError(f"Unsupported OAuth provider: {provider}")
        
        # OAuth users are automatically verified
        user.is_verified = True
        user.updated_at = datetime.utcnow()
        
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    def unlink_oauth_account(
        self,
        db: Session,
        *,
        user: User,
        provider: str
    ) -> User:
        """
        Unlink OAuth account from user.
        """
        if provider == "google":
            user.google_id = None
        elif provider == "apple":
            user.apple_id = None
        else:
            raise ValueError(f"Unsupported OAuth provider: {provider}")
        
        user.updated_at = datetime.utcnow()
        
        db.add(user)
        db.commit()
        db.refresh(user)
        return user


# Create global instance
user_crud = CRUDUser(User)
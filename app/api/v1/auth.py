from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr

from app.core.database import get_db
from app.core.auth import get_current_user_id, create_access_token, verify_token
from app.crud.user import user_crud
from app.schemas.user import User, UserCreate

router = APIRouter()


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class AuthRequest(BaseModel):
    """Request for authentication with NextAuth.js token"""
    token: str


class UserProfileResponse(BaseModel):
    """User profile information"""
    id: str
    email: str
    full_name: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    base_currency: str
    theme_preference: str
    is_verified: bool
    is_premium: bool


@router.post("/validate-token")
async def validate_token(
    *,
    db: Session = Depends(get_db),
    request: AuthRequest
):
    """
    Validate a JWT token from NextAuth.js and return user information.
    This endpoint is used by the frontend to verify tokens and get user data.
    """
    # Verify the token
    payload = verify_token(request.token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user from database
    user = user_crud.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User account is inactive"
        )
    
    # Update last login time
    user_crud.update_last_login(db, user=user)
    
    return {
        "valid": True,
        "user": UserProfileResponse(
            id=str(user.id),
            email=user.email,
            full_name=user.full_name,
            first_name=user.first_name,
            last_name=user.last_name,
            base_currency=user.base_currency,
            theme_preference=user.theme_preference,
            is_verified=user.is_verified,
            is_premium=user.is_premium
        ),
        "token_info": {
            "expires_at": payload.get("exp"),
            "issued_at": payload.get("iat")
        }
    }


@router.post("/create-backend-token", response_model=TokenResponse)
async def create_backend_token(
    *,
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Create a backend-specific access token for API calls.
    This can be used if you want to issue separate tokens for backend API access.
    """
    from datetime import timedelta
    from app.core.config import settings
    
    # Create token with user ID
    access_token = create_access_token(
        data={"sub": current_user_id},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return TokenResponse(
        access_token=access_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60  # Convert to seconds
    )


@router.get("/me", response_model=UserProfileResponse)
async def get_current_user_profile(
    *,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Get current user's profile information.
    """
    user = user_crud.get(db, id=current_user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserProfileResponse(
        id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        first_name=user.first_name,
        last_name=user.last_name,
        base_currency=user.base_currency,
        theme_preference=user.theme_preference,
        is_verified=user.is_verified,
        is_premium=user.is_premium
    )


@router.post("/refresh-token")
async def refresh_token(
    *,
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Refresh an access token.
    Note: In a production system, you'd typically use refresh tokens for this.
    """
    from datetime import timedelta
    from app.core.config import settings
    
    # Create new token
    access_token = create_access_token(
        data={"sub": current_user_id},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return TokenResponse(
        access_token=access_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/logout")
async def logout(
    *,
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Logout endpoint.
    In a stateless JWT system, logout is typically handled by the client
    by simply discarding the token. This endpoint is here for completeness
    and could be extended to implement token blacklisting.
    """
    return {
        "message": "Successfully logged out",
        "user_id": current_user_id
    }


# OAuth integration endpoints (for future use with NextAuth.js)
@router.post("/oauth/google")
async def google_oauth_callback():
    """
    Google OAuth callback endpoint.
    This would be used if handling OAuth directly in the backend.
    For NextAuth.js integration, this is typically not needed.
    """
    return {
        "message": "Google OAuth integration via NextAuth.js",
        "status": "not_implemented"
    }


@router.post("/oauth/apple")
async def apple_oauth_callback():
    """
    Apple OAuth callback endpoint.
    This would be used if handling OAuth directly in the backend.
    For NextAuth.js integration, this is typically not needed.
    """
    return {
        "message": "Apple OAuth integration via NextAuth.js",
        "status": "not_implemented"
    }


@router.get("/health")
async def auth_health():
    """
    Health check for authentication service.
    """
    return {
        "status": "healthy",
        "service": "authentication",
        "features": [
            "jwt_validation",
            "user_profile",
            "token_refresh",
            "nextauth_integration"
        ]
    }
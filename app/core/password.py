from passlib.context import CryptContext

# Initialize bcrypt context for secure password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt with salt.
    This is called when user registers or changes password.
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plaintext password against its bcrypt hash.
    Used during login to validate user credentials.
    """
    return pwd_context.verify(plain_password, hashed_password)


def check_password_strength(password: str) -> dict:
    """
    Check password strength and return detailed analysis.
    Useful for frontend password strength indicators.
    """
    checks = {
        "min_length": len(password) >= 8,
        "has_uppercase": any(c.isupper() for c in password),
        "has_lowercase": any(c.islower() for c in password),
        "has_digit": any(c.isdigit() for c in password),
        "has_special": any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
    }
    
    score = sum(checks.values())
    
    # Determine strength level
    if score < 3:
        strength = "weak"
    elif score < 5:
        strength = "medium" 
    else:
        strength = "strong"
    
    return {
        "score": score,
        "max_score": len(checks),
        "checks": checks,
        "strength": strength,
        "is_valid": score >= 4  # Require at least 4/5 criteria
    }

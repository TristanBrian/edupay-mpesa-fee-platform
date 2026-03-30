"""
Security utilities for FlexiFees API
Includes JWT authentication, password hashing, and security helpers
"""
import hashlib
import hmac
import secrets
import re
from datetime import datetime, timedelta, timezone
from typing import Optional, Annotated
from functools import wraps

from fastapi import Depends, HTTPException, status, Request, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..config import get_settings

settings = get_settings()


# =============================================================================
# Configuration
# =============================================================================

# JWT Settings - In production, these should be in environment variables
SECRET_KEY = getattr(settings, 'secret_key', secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security schemes
bearer_scheme = HTTPBearer(auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


# =============================================================================
# Models
# =============================================================================

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    user_id: Optional[int] = None
    username: Optional[str] = None
    role: Optional[str] = None
    school_id: Optional[int] = None
    scopes: list[str] = Field(default_factory=list)


class UserRole:
    ADMIN = "admin"
    SCHOOL_ADMIN = "school_admin"
    GUARDIAN = "guardian"
    STAFF = "staff"
    READONLY = "readonly"


# Role-based permissions
ROLE_PERMISSIONS = {
    UserRole.ADMIN: [
        "payments:read", "payments:write", "payments:delete",
        "schools:read", "schools:write", "schools:delete",
        "students:read", "students:write", "students:delete",
        "guardians:read", "guardians:write", "guardians:delete",
        "invoices:read", "invoices:write", "invoices:delete",
        "analytics:read", "users:read", "users:write", "users:delete",
    ],
    UserRole.SCHOOL_ADMIN: [
        "payments:read", "payments:write",
        "schools:read",
        "students:read", "students:write",
        "guardians:read", "guardians:write",
        "invoices:read", "invoices:write",
        "analytics:read",
    ],
    UserRole.STAFF: [
        "payments:read",
        "schools:read",
        "students:read",
        "guardians:read",
        "invoices:read",
    ],
    UserRole.GUARDIAN: [
        "payments:read", "payments:write",
        "students:read",
        "invoices:read",
    ],
    UserRole.READONLY: [
        "payments:read",
        "schools:read",
        "students:read",
        "invoices:read",
    ],
}


# =============================================================================
# Password Utilities
# =============================================================================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password for storage."""
    return pwd_context.hash(password)


def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Validate password strength requirements.
    Returns (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r"\d", password):
        return False, "Password must contain at least one digit"
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain at least one special character"
    return True, ""


# =============================================================================
# JWT Token Utilities
# =============================================================================

def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create a new access token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access"
    })
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(data: dict) -> str:
    """Create a new refresh token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "refresh"
    })
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[TokenData]:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        username: str = payload.get("username")
        role: str = payload.get("role")
        school_id: int = payload.get("school_id")
        scopes: list = payload.get("scopes", [])
        
        if user_id is None:
            return None
            
        return TokenData(
            user_id=user_id,
            username=username,
            role=role,
            school_id=school_id,
            scopes=scopes
        )
    except JWTError:
        return None


def create_tokens(user_id: int, username: str, role: str, school_id: Optional[int] = None) -> Token:
    """Create both access and refresh tokens for a user."""
    scopes = ROLE_PERMISSIONS.get(role, [])
    
    token_data = {
        "sub": user_id,
        "username": username,
        "role": role,
        "school_id": school_id,
        "scopes": scopes
    }
    
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


# =============================================================================
# Authentication Dependencies
# =============================================================================

async def get_current_user(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(bearer_scheme)],
    api_key: Annotated[Optional[str], Depends(api_key_header)],
) -> TokenData:
    """
    Get the current authenticated user from JWT token or API key.
    Raises HTTPException if authentication fails.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Try JWT token first
    if credentials and credentials.credentials:
        token_data = decode_token(credentials.credentials)
        if token_data:
            return token_data
    
    # Try API key
    if api_key:
        # In production, validate API key against database
        api_key_settings = getattr(settings, 'api_keys', {})
        if api_key in api_key_settings:
            return TokenData(
                user_id=0,
                username="api_client",
                role=api_key_settings[api_key].get("role", UserRole.READONLY),
                scopes=api_key_settings[api_key].get("scopes", [])
            )
    
    raise credentials_exception


async def get_current_user_optional(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(bearer_scheme)],
    api_key: Annotated[Optional[str], Depends(api_key_header)],
) -> Optional[TokenData]:
    """
    Get the current user if authenticated, None otherwise.
    Does not raise exceptions for unauthenticated requests.
    """
    try:
        return await get_current_user(credentials, api_key)
    except HTTPException:
        return None


def require_permissions(*required_scopes: str):
    """
    Dependency factory that checks if the user has required permissions.
    Usage: Depends(require_permissions("payments:write", "invoices:read"))
    """
    async def permission_checker(
        current_user: Annotated[TokenData, Depends(get_current_user)]
    ) -> TokenData:
        if current_user.role == UserRole.ADMIN:
            return current_user
            
        user_scopes = set(current_user.scopes)
        required = set(required_scopes)
        
        if not required.issubset(user_scopes):
            missing = required - user_scopes
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Missing: {', '.join(missing)}"
            )
        return current_user
    
    return permission_checker


def require_role(*allowed_roles: str):
    """
    Dependency factory that checks if the user has one of the allowed roles.
    Usage: Depends(require_role(UserRole.ADMIN, UserRole.SCHOOL_ADMIN))
    """
    async def role_checker(
        current_user: Annotated[TokenData, Depends(get_current_user)]
    ) -> TokenData:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join(allowed_roles)}"
            )
        return current_user
    
    return role_checker


# =============================================================================
# M-Pesa Security Utilities
# =============================================================================

def verify_mpesa_signature(
    payload: bytes,
    signature: str,
    secret_key: str
) -> bool:
    """
    Verify M-Pesa callback signature using HMAC-SHA256.
    This ensures the callback is genuinely from Safaricom.
    """
    expected_signature = hmac.new(
        secret_key.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature.lower(), expected_signature.lower())


def generate_mpesa_security_credential(initiator_password: str, certificate_path: str) -> str:
    """
    Generate security credential for M-Pesa B2C/B2B transactions.
    Uses RSA encryption with Safaricom's public certificate.
    """
    from cryptography.hazmat.primitives import serialization, hashes
    from cryptography.hazmat.primitives.asymmetric import padding
    from cryptography import x509
    import base64
    
    with open(certificate_path, 'rb') as cert_file:
        cert = x509.load_pem_x509_certificate(cert_file.read())
    
    public_key = cert.public_key()
    encrypted = public_key.encrypt(
        initiator_password.encode(),
        padding.PKCS1v15()
    )
    
    return base64.b64encode(encrypted).decode()


class MPesaCallbackValidator:
    """Validator for M-Pesa callback requests."""
    
    # Known Safaricom IP ranges (should be updated regularly)
    SAFARICOM_IPS = [
        "196.201.214.",
        "196.201.215.",
        "41.223.58.",
        "105.160.12.",
    ]
    
    @classmethod
    def validate_ip(cls, client_ip: str) -> bool:
        """Check if the request comes from known Safaricom IP ranges."""
        return any(client_ip.startswith(ip) for ip in cls.SAFARICOM_IPS)
    
    @staticmethod
    def validate_callback_structure(data: dict) -> tuple[bool, str]:
        """Validate the callback data structure."""
        if "Body" not in data:
            return False, "Missing 'Body' field"
        
        body = data.get("Body", {})
        if "stkCallback" not in body:
            return False, "Missing 'stkCallback' field"
        
        callback = body.get("stkCallback", {})
        required_fields = ["MerchantRequestID", "CheckoutRequestID", "ResultCode"]
        
        for field in required_fields:
            if field not in callback:
                return False, f"Missing required field: {field}"
        
        return True, ""


# =============================================================================
# Request Security Utilities  
# =============================================================================

def sanitize_sql_like(value: str) -> str:
    """
    Sanitize a value for use in SQL LIKE queries.
    Escapes special LIKE characters.
    """
    # Escape special LIKE characters
    sanitized = value.replace("\\", "\\\\")
    sanitized = sanitized.replace("%", "\\%")
    sanitized = sanitized.replace("_", "\\_")
    return sanitized


def generate_secure_token(length: int = 32) -> str:
    """Generate a cryptographically secure random token."""
    return secrets.token_urlsafe(length)


def constant_time_compare(val1: str, val2: str) -> bool:
    """Compare two strings in constant time to prevent timing attacks."""
    return hmac.compare_digest(val1.encode(), val2.encode())


class SecurityUtils:
    """Collection of security utility methods."""
    
    @staticmethod
    def mask_phone(phone: str) -> str:
        """Mask a phone number for logging (shows last 4 digits)."""
        if len(phone) > 4:
            return "*" * (len(phone) - 4) + phone[-4:]
        return "****"
    
    @staticmethod
    def mask_email(email: str) -> str:
        """Mask an email for logging."""
        if "@" in email:
            local, domain = email.split("@", 1)
            if len(local) > 2:
                masked_local = local[0] + "*" * (len(local) - 2) + local[-1]
            else:
                masked_local = "*" * len(local)
            return f"{masked_local}@{domain}"
        return "****"
    
    @staticmethod
    def is_safe_redirect(url: str, allowed_hosts: list[str]) -> bool:
        """Check if a URL is safe for redirecting."""
        from urllib.parse import urlparse
        
        if not url:
            return False
        
        parsed = urlparse(url)
        
        # Relative URLs are safe
        if not parsed.netloc:
            return True
        
        # Check against allowed hosts
        return parsed.netloc in allowed_hosts

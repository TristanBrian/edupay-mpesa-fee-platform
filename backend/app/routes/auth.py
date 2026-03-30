"""
Authentication routes for FlexiFees API
"""
import hashlib
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Annotated

from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field, EmailStr, field_validator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from ..models.database import get_db
from ..models.user import User, RefreshToken, LoginAttempt, AuditLog
from ..core.security import (
    verify_password,
    get_password_hash,
    validate_password_strength,
    create_tokens,
    decode_token,
    get_current_user,
    TokenData,
    Token,
    UserRole,
    generate_secure_token,
)
from .schemas import sanitize_string

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])


# =============================================================================
# Request/Response Models
# =============================================================================

class UserRegister(BaseModel):
    """User registration request."""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    
    @field_validator('username')
    @classmethod
    def sanitize_username(cls, v: str) -> str:
        return sanitize_string(v.lower())


class UserLogin(BaseModel):
    """User login request."""
    username: str
    password: str


class UserResponse(BaseModel):
    """User response model."""
    id: int
    username: str
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    role: str
    school_id: Optional[int]
    is_active: bool
    is_verified: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class PasswordChange(BaseModel):
    """Password change request."""
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)


class PasswordReset(BaseModel):
    """Password reset request."""
    email: EmailStr


class RefreshTokenRequest(BaseModel):
    """Refresh token request."""
    refresh_token: str


# =============================================================================
# Security Helpers
# =============================================================================

MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 15


async def check_account_lockout(user: User) -> tuple[bool, Optional[str]]:
    """Check if user account is locked."""
    if user.locked_until and user.locked_until > datetime.utcnow():
        remaining = (user.locked_until - datetime.utcnow()).seconds // 60
        return True, f"Account locked. Try again in {remaining + 1} minutes."
    return False, None


async def record_login_attempt(
    db: AsyncSession,
    username: str,
    ip_address: str,
    user_agent: str,
    success: bool,
    failure_reason: Optional[str] = None
):
    """Record a login attempt for security monitoring."""
    attempt = LoginAttempt(
        username=username,
        ip_address=ip_address,
        user_agent=user_agent,
        success=success,
        failure_reason=failure_reason
    )
    db.add(attempt)
    await db.commit()


async def audit_log(
    db: AsyncSession,
    action: str,
    user_id: Optional[int] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    details: Optional[str] = None,
    status: str = "success",
    error_message: Optional[str] = None
):
    """Create an audit log entry."""
    log = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        ip_address=ip_address,
        user_agent=user_agent,
        details=details,
        status=status,
        error_message=error_message
    )
    db.add(log)
    await db.commit()


def get_client_ip(request: Request) -> str:
    """Extract client IP from request headers."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


# =============================================================================
# Routes
# =============================================================================

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user account.
    New users start with 'readonly' role and must be promoted by an admin.
    """
    # Validate password strength
    is_valid, error_msg = validate_password_strength(user_data.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    
    # Check if username exists
    existing = await db.execute(
        select(User).where(User.username == user_data.username)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already registered"
        )
    
    # Check if email exists
    existing_email = await db.execute(
        select(User).where(User.email == user_data.email)
    )
    if existing_email.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )
    
    # Create user
    user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        phone=user_data.phone,
        role=UserRole.READONLY,  # Default role
        is_active=True,
        is_verified=False
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    # Audit log
    await audit_log(
        db,
        action="user_registered",
        user_id=user.id,
        resource_type="user",
        resource_id=str(user.id),
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
        details=f"User {user.username} registered"
    )
    
    logger.info(f"New user registered: {user.username}")
    return user


@router.post("/login", response_model=Token)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticate user and return JWT tokens.
    Uses OAuth2 password flow for compatibility.
    """
    ip_address = get_client_ip(request)
    user_agent = request.headers.get("User-Agent", "")
    
    # Find user
    result = await db.execute(
        select(User).where(User.username == form_data.username)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        await record_login_attempt(
            db, form_data.username, ip_address, user_agent,
            success=False, failure_reason="user_not_found"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if account is locked
    is_locked, lock_msg = await check_account_lockout(user)
    if is_locked:
        await record_login_attempt(
            db, form_data.username, ip_address, user_agent,
            success=False, failure_reason="account_locked"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=lock_msg
        )
    
    # Verify password
    if not verify_password(form_data.password, user.hashed_password):
        # Increment failed attempts
        user.failed_login_attempts += 1
        
        # Lock account if too many failures
        if user.failed_login_attempts >= MAX_LOGIN_ATTEMPTS:
            user.locked_until = datetime.utcnow() + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
            logger.warning(f"Account locked due to failed attempts: {user.username}")
        
        await db.commit()
        
        await record_login_attempt(
            db, form_data.username, ip_address, user_agent,
            success=False, failure_reason="invalid_password"
        )
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if not user.is_active:
        await record_login_attempt(
            db, form_data.username, ip_address, user_agent,
            success=False, failure_reason="account_disabled"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled"
        )
    
    # Success - reset failed attempts
    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login = datetime.utcnow()
    await db.commit()
    
    # Create tokens
    tokens = create_tokens(
        user_id=user.id,
        username=user.username,
        role=user.role,
        school_id=user.school_id
    )
    
    # Store refresh token hash
    token_hash = hashlib.sha256(tokens.refresh_token.encode()).hexdigest()
    refresh_token = RefreshToken(
        user_id=user.id,
        token_hash=token_hash,
        device_info=user_agent[:255] if user_agent else None,
        ip_address=ip_address,
        expires_at=datetime.utcnow() + timedelta(days=7)
    )
    db.add(refresh_token)
    await db.commit()
    
    await record_login_attempt(
        db, form_data.username, ip_address, user_agent,
        success=True
    )
    
    await audit_log(
        db,
        action="user_login",
        user_id=user.id,
        resource_type="session",
        ip_address=ip_address,
        user_agent=user_agent,
        details="Successful login"
    )
    
    logger.info(f"User logged in: {user.username}")
    return tokens


@router.post("/refresh", response_model=Token)
async def refresh_token(
    request: Request,
    token_request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Refresh access token using refresh token.
    Implements token rotation for security.
    """
    # Decode the refresh token
    token_data = decode_token(token_request.refresh_token)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    # Find the stored refresh token
    token_hash = hashlib.sha256(token_request.refresh_token.encode()).hexdigest()
    result = await db.execute(
        select(RefreshToken).where(
            and_(
                RefreshToken.token_hash == token_hash,
                RefreshToken.revoked == False,
                RefreshToken.expires_at > datetime.utcnow()
            )
        )
    )
    stored_token = result.scalar_one_or_none()
    
    if not stored_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found or expired"
        )
    
    # Get user
    result = await db.execute(
        select(User).where(User.id == stored_token.user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    # Revoke old token (token rotation)
    stored_token.revoked = True
    stored_token.revoked_at = datetime.utcnow()
    
    # Create new tokens
    tokens = create_tokens(
        user_id=user.id,
        username=user.username,
        role=user.role,
        school_id=user.school_id
    )
    
    # Store new refresh token
    new_token_hash = hashlib.sha256(tokens.refresh_token.encode()).hexdigest()
    new_refresh_token = RefreshToken(
        user_id=user.id,
        token_hash=new_token_hash,
        device_info=request.headers.get("User-Agent", "")[:255],
        ip_address=get_client_ip(request),
        expires_at=datetime.utcnow() + timedelta(days=7)
    )
    db.add(new_refresh_token)
    await db.commit()
    
    logger.info(f"Token refreshed for user: {user.username}")
    return tokens


@router.post("/logout")
async def logout(
    request: Request,
    current_user: Annotated[TokenData, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """
    Logout user by revoking all refresh tokens.
    """
    # Revoke all refresh tokens for user
    result = await db.execute(
        select(RefreshToken).where(
            and_(
                RefreshToken.user_id == current_user.user_id,
                RefreshToken.revoked == False
            )
        )
    )
    tokens = result.scalars().all()
    
    for token in tokens:
        token.revoked = True
        token.revoked_at = datetime.utcnow()
    
    await db.commit()
    
    await audit_log(
        db,
        action="user_logout",
        user_id=current_user.user_id,
        resource_type="session",
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
        details="User logged out"
    )
    
    logger.info(f"User logged out: {current_user.username}")
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: Annotated[TokenData, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """Get current authenticated user information."""
    result = await db.execute(
        select(User).where(User.id == current_user.user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user


@router.post("/change-password")
async def change_password(
    request: Request,
    password_data: PasswordChange,
    current_user: Annotated[TokenData, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """Change the current user's password."""
    # Get user
    result = await db.execute(
        select(User).where(User.id == current_user.user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Verify current password
    if not verify_password(password_data.current_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Validate new password
    is_valid, error_msg = validate_password_strength(password_data.new_password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    
    # Update password
    user.hashed_password = get_password_hash(password_data.new_password)
    user.password_changed_at = datetime.utcnow()
    
    # Revoke all refresh tokens (force re-login on all devices)
    result = await db.execute(
        select(RefreshToken).where(
            and_(
                RefreshToken.user_id == user.id,
                RefreshToken.revoked == False
            )
        )
    )
    tokens = result.scalars().all()
    for token in tokens:
        token.revoked = True
        token.revoked_at = datetime.utcnow()
    
    await db.commit()
    
    await audit_log(
        db,
        action="password_changed",
        user_id=user.id,
        resource_type="user",
        resource_id=str(user.id),
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
        details="Password changed by user"
    )
    
    logger.info(f"Password changed for user: {user.username}")
    return {"message": "Password changed successfully"}


@router.get("/sessions")
async def list_active_sessions(
    current_user: Annotated[TokenData, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """List all active sessions for the current user."""
    result = await db.execute(
        select(RefreshToken).where(
            and_(
                RefreshToken.user_id == current_user.user_id,
                RefreshToken.revoked == False,
                RefreshToken.expires_at > datetime.utcnow()
            )
        )
    )
    tokens = result.scalars().all()
    
    return [
        {
            "id": token.id,
            "device_info": token.device_info,
            "ip_address": token.ip_address,
            "created_at": token.created_at,
            "expires_at": token.expires_at
        }
        for token in tokens
    ]


@router.delete("/sessions/{session_id}")
async def revoke_session(
    session_id: int,
    request: Request,
    current_user: Annotated[TokenData, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """Revoke a specific session."""
    result = await db.execute(
        select(RefreshToken).where(
            and_(
                RefreshToken.id == session_id,
                RefreshToken.user_id == current_user.user_id
            )
        )
    )
    token = result.scalar_one_or_none()
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    token.revoked = True
    token.revoked_at = datetime.utcnow()
    await db.commit()
    
    await audit_log(
        db,
        action="session_revoked",
        user_id=current_user.user_id,
        resource_type="session",
        resource_id=str(session_id),
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
        details="Session manually revoked"
    )
    
    return {"message": "Session revoked successfully"}

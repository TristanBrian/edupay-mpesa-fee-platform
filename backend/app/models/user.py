"""
User model for authentication
"""
from sqlalchemy import Column, String, Integer, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from .payment import Base


class User(Base):
    """User model for authentication and authorization."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    
    # Profile
    first_name = Column(String(100))
    last_name = Column(String(100))
    phone = Column(String(20))
    
    # Role-based access
    role = Column(String(50), default="readonly", nullable=False)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=True)
    guardian_id = Column(Integer, ForeignKey("guardians.id"), nullable=True)
    
    # Account status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # Security
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)
    last_login = Column(DateTime, nullable=True)
    password_changed_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    school = relationship("School", backref="users")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")


class RefreshToken(Base):
    """Store refresh tokens for token rotation."""
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash = Column(String(255), unique=True, nullable=False, index=True)
    
    # Token metadata
    device_info = Column(String(255))
    ip_address = Column(String(45))  # IPv6 compatible
    
    # Expiration
    expires_at = Column(DateTime, nullable=False)
    revoked = Column(Boolean, default=False)
    revoked_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="refresh_tokens")


class APIKey(Base):
    """API Key storage for machine-to-machine authentication."""
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    key_hash = Column(String(255), unique=True, nullable=False, index=True)
    key_prefix = Column(String(10), nullable=False)  # First 8 chars for identification
    
    # Permissions
    role = Column(String(50), default="readonly", nullable=False)
    scopes = Column(String(1000))  # Comma-separated scopes
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=True)
    
    # Rate limiting
    rate_limit = Column(Integer, default=1000)  # Requests per hour
    
    # Status
    is_active = Column(Boolean, default=True)
    last_used_at = Column(DateTime, nullable=True)
    
    # Expiration
    expires_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    school = relationship("School", backref="api_keys")


class AuditLog(Base):
    """Audit log for tracking security-sensitive operations."""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    
    # Actor
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    api_key_id = Column(Integer, ForeignKey("api_keys.id", ondelete="SET NULL"), nullable=True)
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    
    # Action
    action = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(100), index=True)  # e.g., "payment", "user", "invoice"
    resource_id = Column(String(100))
    
    # Details
    old_value = Column(String(5000))  # JSON string of old values
    new_value = Column(String(5000))  # JSON string of new values
    details = Column(String(1000))    # Additional context
    
    # Status
    status = Column(String(20), default="success")  # success, failure, blocked
    error_message = Column(String(500))
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")


class LoginAttempt(Base):
    """Track login attempts for security monitoring."""
    __tablename__ = "login_attempts"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), index=True)
    ip_address = Column(String(45), index=True)
    user_agent = Column(String(500))
    
    # Result
    success = Column(Boolean, default=False)
    failure_reason = Column(String(100))
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

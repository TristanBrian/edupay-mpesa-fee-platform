"""
Security Utilities
Provides input validation, sanitization, audit logging, and security helpers.
Addresses cybersecurity team requirements.
"""

import re
import hashlib
import hmac
import secrets
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from functools import wraps
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..models.payment import AuditLog

logger = logging.getLogger(__name__)


# ============== INPUT VALIDATION ==============

class InputValidator:
    """
    Comprehensive input validation for API requests.
    Prevents injection attacks and ensures data integrity.
    """
    
    # Patterns for validation
    PHONE_PATTERN = re.compile(r'^254\d{9}$')
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    ALPHANUMERIC_PATTERN = re.compile(r'^[a-zA-Z0-9\s\-_]+$')
    ID_NUMBER_PATTERN = re.compile(r'^[a-zA-Z0-9]+$')
    
    # Dangerous patterns to block
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|ALTER|CREATE|TRUNCATE)\b)",
        r"(--|#|\/\*|\*\/)",
        r"(\bOR\b\s+\d+\s*=\s*\d+)",
        r"(\bAND\b\s+\d+\s*=\s*\d+)",
        r"(;|\||\$|`)",
    ]
    
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe[^>]*>",
        r"<object[^>]*>",
        r"<embed[^>]*>",
    ]
    
    @classmethod
    def validate_phone(cls, phone: str) -> tuple[bool, str]:
        """Validate Kenyan phone number format."""
        if not phone:
            return False, "Phone number is required"
        
        # Clean the phone number
        cleaned = re.sub(r'[\s\-\(\)]', '', phone)
        
        # Convert to 254 format
        if cleaned.startswith('0'):
            cleaned = '254' + cleaned[1:]
        elif cleaned.startswith('+'):
            cleaned = cleaned[1:]
        
        if not cls.PHONE_PATTERN.match(cleaned):
            return False, "Invalid phone number format. Use 254XXXXXXXXX"
        
        return True, cleaned
    
    @classmethod
    def validate_email(cls, email: str) -> tuple[bool, str]:
        """Validate email address format."""
        if not email:
            return True, email  # Email is optional
        
        email = email.strip().lower()
        
        if not cls.EMAIL_PATTERN.match(email):
            return False, "Invalid email format"
        
        return True, email
    
    @classmethod
    def sanitize_string(cls, value: str, max_length: int = 255) -> str:
        """
        Sanitize string input to prevent injection attacks.
        Removes dangerous characters and limits length.
        """
        if not value:
            return value
        
        # Trim whitespace
        value = value.strip()
        
        # Remove null bytes
        value = value.replace('\x00', '')
        
        # Remove control characters
        value = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', value)
        
        # Escape HTML entities
        value = cls.escape_html(value)
        
        # Limit length
        if len(value) > max_length:
            value = value[:max_length]
        
        return value
    
    @classmethod
    def escape_html(cls, value: str) -> str:
        """Escape HTML special characters."""
        if not value:
            return value
        
        replacements = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#x27;',
            '/': '&#x2F;',
        }
        
        for char, replacement in replacements.items():
            value = value.replace(char, replacement)
        
        return value
    
    @classmethod
    def check_sql_injection(cls, value: str) -> bool:
        """
        Check for potential SQL injection patterns.
        Returns True if injection attempt detected.
        """
        if not value:
            return False
        
        value_upper = value.upper()
        
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, value_upper, re.IGNORECASE):
                logger.warning(f"Potential SQL injection detected: {value[:100]}")
                return True
        
        return False
    
    @classmethod
    def check_xss(cls, value: str) -> bool:
        """
        Check for potential XSS patterns.
        Returns True if XSS attempt detected.
        """
        if not value:
            return False
        
        for pattern in cls.XSS_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                logger.warning(f"Potential XSS detected: {value[:100]}")
                return True
        
        return False
    
    @classmethod
    def validate_amount(cls, amount: int, min_amount: int = 1, max_amount: int = 150000) -> tuple[bool, str]:
        """Validate payment amount within M-Pesa limits."""
        if not isinstance(amount, int):
            return False, "Amount must be an integer"
        
        if amount < min_amount:
            return False, f"Amount must be at least {min_amount}"
        
        if amount > max_amount:
            return False, f"Amount cannot exceed {max_amount}"
        
        return True, str(amount)
    
    @classmethod
    def validate_account_reference(cls, reference: str) -> tuple[bool, str]:
        """Validate account reference for M-Pesa."""
        if not reference:
            return False, "Account reference is required"
        
        # Sanitize
        reference = cls.sanitize_string(reference, max_length=20)
        
        # Check for dangerous patterns
        if cls.check_sql_injection(reference) or cls.check_xss(reference):
            return False, "Invalid characters in account reference"
        
        return True, reference


# ============== MPESA CREDENTIAL PROTECTION ==============

class MpesaCredentialManager:
    """
    Secure handling of M-Pesa credentials.
    Ensures credentials are never exposed in logs or responses.
    """
    
    # List of sensitive field names to mask
    SENSITIVE_FIELDS = [
        'mpesa_consumer_key',
        'mpesa_consumer_secret',
        'mpesa_passkey',
        'password',
        'access_token',
        'api_key',
        'secret_key',
        'private_key',
    ]
    
    @classmethod
    def mask_sensitive_data(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Mask sensitive fields in a dictionary.
        Returns a new dictionary with masked values.
        """
        if not isinstance(data, dict):
            return data
        
        masked = {}
        for key, value in data.items():
            if any(sensitive in key.lower() for sensitive in cls.SENSITIVE_FIELDS):
                if isinstance(value, str) and len(value) > 4:
                    masked[key] = value[:2] + '*' * (len(value) - 4) + value[-2:]
                else:
                    masked[key] = '****'
            elif isinstance(value, dict):
                masked[key] = cls.mask_sensitive_data(value)
            elif isinstance(value, list):
                masked[key] = [cls.mask_sensitive_data(item) if isinstance(item, dict) else item for item in value]
            else:
                masked[key] = value
        
        return masked
    
    @classmethod
    def validate_callback_signature(cls, payload: dict, signature: str, secret_key: str) -> bool:
        """
        Validate M-Pesa callback signature.
        Ensures callback is from legitimate M-Pesa servers.
        """
        if not signature or not secret_key:
            return False
        
        # Create signature from payload
        import json
        payload_string = json.dumps(payload, sort_keys=True)
        expected_signature = hmac.new(
            secret_key.encode(),
            payload_string.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature.lower(), expected_signature.lower())
    
    @classmethod
    def generate_secure_token(cls, length: int = 32) -> str:
        """Generate a cryptographically secure token."""
        return secrets.token_hex(length)


# ============== AUDIT LOGGING ==============

class AuditLogger:
    """
    Security audit logging for compliance and incident investigation.
    Logs all sensitive operations with context.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def log(
        self,
        action: str,
        resource_type: str,
        resource_id: Optional[int] = None,
        actor_type: str = "user",
        actor_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_method: Optional[str] = None,
        request_path: Optional[str] = None,
        request_body: Optional[dict] = None,
        response_status: Optional[int] = None,
        response_body: Optional[dict] = None,
        details: Optional[dict] = None
    ):
        """
        Log an audit event to the database.
        """
        try:
            # Mask sensitive data in request/response
            masked_request = MpesaCredentialManager.mask_sensitive_data(request_body) if request_body else None
            masked_response = MpesaCredentialManager.mask_sensitive_data(response_body) if response_body else None
            
            audit_log = AuditLog(
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                actor_type=actor_type,
                actor_id=actor_id,
                ip_address=ip_address,
                user_agent=user_agent[:500] if user_agent else None,
                request_method=request_method,
                request_path=request_path[:500] if request_path else None,
                request_body=masked_request,
                response_status=response_status,
                response_body=masked_response,
                details=details
            )
            
            self.db.add(audit_log)
            await self.db.commit()
            
            # Also log to application logs
            logger.info(f"AUDIT: {action} on {resource_type}:{resource_id} by {actor_type}:{actor_id}")
            
        except Exception as e:
            logger.error(f"Failed to write audit log: {str(e)}")
            # Don't raise - audit logging failure shouldn't break the application
    
    async def log_payment_initiation(
        self,
        payment_id: int,
        amount: int,
        phone: str,
        ip_address: str = None
    ):
        """Log payment initiation event."""
        await self.log(
            action="payment_initiated",
            resource_type="payment",
            resource_id=payment_id,
            actor_type="system",
            ip_address=ip_address,
            details={
                "amount": amount,
                "phone_masked": phone[:6] + "****" + phone[-2:] if len(phone) > 8 else "****"
            }
        )
    
    async def log_payment_completion(
        self,
        payment_id: int,
        status: str,
        mpesa_receipt: Optional[str] = None
    ):
        """Log payment completion event."""
        await self.log(
            action="payment_completed",
            resource_type="payment",
            resource_id=payment_id,
            actor_type="mpesa",
            details={
                "status": status,
                "mpesa_receipt": mpesa_receipt
            }
        )
    
    async def log_loan_action(
        self,
        action: str,
        loan_id: int,
        actor_id: str,
        details: dict = None
    ):
        """Log loan-related actions."""
        await self.log(
            action=action,
            resource_type="loan",
            resource_id=loan_id,
            actor_type="user",
            actor_id=actor_id,
            details=details
        )
    
    async def log_security_event(
        self,
        event_type: str,
        ip_address: str,
        details: dict = None
    ):
        """Log security events (failed auth, rate limiting, etc.)."""
        await self.log(
            action=event_type,
            resource_type="security",
            actor_type="system",
            ip_address=ip_address,
            details=details
        )


# ============== REQUEST VALIDATION MIDDLEWARE ==============

class SecurityMiddleware:
    """
    Additional security checks for incoming requests.
    """
    
    # Blocked user agents (bots, scanners)
    BLOCKED_USER_AGENTS = [
        'sqlmap',
        'nikto',
        'nmap',
        'masscan',
        'burp',
    ]
    
    # IP reputation (would be loaded from external service in production)
    BLOCKED_IPS: List[str] = []
    
    @classmethod
    def check_user_agent(cls, user_agent: str) -> bool:
        """
        Check if user agent is blocked.
        Returns True if blocked.
        """
        if not user_agent:
            return False
        
        user_agent_lower = user_agent.lower()
        return any(blocked in user_agent_lower for blocked in cls.BLOCKED_USER_AGENTS)
    
    @classmethod
    def check_ip(cls, ip_address: str) -> bool:
        """
        Check if IP is blocked.
        Returns True if blocked.
        """
        return ip_address in cls.BLOCKED_IPS
    
    @classmethod
    def validate_content_type(cls, content_type: str, expected: str = "application/json") -> bool:
        """Validate Content-Type header."""
        if not content_type:
            return False
        return expected in content_type.lower()


# ============== ENV PROTECTION ==============

def check_env_security():
    """
    Check that environment is properly secured.
    Logs warnings for potential issues.
    """
    import os
    
    warnings = []
    
    # Check for default/mock credentials
    if os.getenv('MPESA_CONSUMER_KEY') == 'mock_key':
        warnings.append("M-Pesa consumer key is using default mock value")
    
    if os.getenv('MPESA_CONSUMER_SECRET') == 'mock_secret':
        warnings.append("M-Pesa consumer secret is using default mock value")
    
    # Check environment
    env = os.getenv('ENVIRONMENT', 'sandbox')
    if env == 'production':
        if os.getenv('DEBUG', 'False').lower() == 'true':
            warnings.append("DEBUG is enabled in production environment")
        
        if os.getenv('MOCK_MPESA', 'False').lower() == 'true':
            warnings.append("Mock M-Pesa is enabled in production environment")
    
    # Log warnings
    for warning in warnings:
        logger.warning(f"SECURITY WARNING: {warning}")
    
    return warnings


# ============== UTILITY FUNCTIONS ==============

def generate_transaction_id() -> str:
    """Generate a secure unique transaction ID."""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_part = secrets.token_hex(6).upper()
    return f"TXN{timestamp}{random_part}"


def hash_phone_number(phone: str) -> str:
    """Hash phone number for logging purposes."""
    return hashlib.sha256(phone.encode()).hexdigest()[:16]


def validate_and_sanitize_request(data: dict) -> tuple[bool, dict, List[str]]:
    """
    Validate and sanitize an entire request dictionary.
    Returns (is_valid, sanitized_data, errors).
    """
    errors = []
    sanitized = {}
    
    for key, value in data.items():
        if isinstance(value, str):
            # Check for injection attempts
            if InputValidator.check_sql_injection(value):
                errors.append(f"Invalid input in field '{key}'")
                continue
            
            if InputValidator.check_xss(value):
                errors.append(f"Invalid input in field '{key}'")
                continue
            
            # Sanitize
            sanitized[key] = InputValidator.sanitize_string(value)
        else:
            sanitized[key] = value
    
    return len(errors) == 0, sanitized, errors

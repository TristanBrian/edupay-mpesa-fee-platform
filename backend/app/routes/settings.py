"""
Settings Routes - M-Pesa Configuration Management
Securely manage API credentials from the frontend
"""
import os
import json
import secrets
import logging
from pathlib import Path
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..services.mpesa import mpesa_service
from ..config import get_settings

router = APIRouter(prefix="/settings", tags=["settings"])
settings = get_settings()
logger = logging.getLogger(__name__)

# Secure credentials file path (outside web root)
CREDENTIALS_FILE = Path(__file__).parent.parent.parent / ".credentials" / "mpesa.json"


class MpesaCredentials(BaseModel):
    """M-Pesa credentials input model"""
    consumer_key: str = Field(..., min_length=10, description="Daraja Consumer Key")
    consumer_secret: str = Field(..., min_length=10, description="Daraja Consumer Secret")
    environment: str = Field(default="sandbox", description="sandbox or production")
    callback_url: Optional[str] = Field(default=None, description="Callback URL for STK Push")


class MpesaCredentialsResponse(BaseModel):
    """M-Pesa credentials response (masked)"""
    consumer_key_set: bool
    consumer_secret_set: bool
    environment: str
    callback_url: str
    shortcode: str
    is_configured: bool
    last_updated: Optional[str] = None


class TestConnectionResponse(BaseModel):
    """Test connection response"""
    success: bool
    message: str
    access_token_obtained: bool = False
    environment: str = ""


def _mask_key(key: str) -> str:
    """Mask API key for display"""
    if not key or len(key) < 8:
        return "****"
    return f"{key[:4]}****{key[-4:]}"


def _ensure_credentials_dir():
    """Ensure credentials directory exists"""
    CREDENTIALS_FILE.parent.mkdir(parents=True, exist_ok=True)


def _load_credentials() -> dict:
    """Load credentials from secure file"""
    if not CREDENTIALS_FILE.exists():
        return {}
    try:
        with open(CREDENTIALS_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading credentials: {e}")
        return {}


def _save_credentials(creds: dict):
    """Save credentials to secure file"""
    _ensure_credentials_dir()
    
    # Add metadata
    creds["last_updated"] = datetime.utcnow().isoformat()
    
    try:
        with open(CREDENTIALS_FILE, "w") as f:
            json.dump(creds, f, indent=2)
        
        # Set restrictive permissions (owner read/write only)
        os.chmod(CREDENTIALS_FILE, 0o600)
        logger.info("Credentials saved successfully")
    except Exception as e:
        logger.error(f"Error saving credentials: {e}")
        raise


@router.get("/mpesa", response_model=MpesaCredentialsResponse)
async def get_mpesa_settings():
    """
    Get current M-Pesa configuration status (credentials masked)
    """
    # First check saved credentials file
    saved = _load_credentials()
    
    # Fall back to environment variables
    consumer_key = saved.get("consumer_key") or settings.mpesa_consumer_key
    consumer_secret = saved.get("consumer_secret") or settings.mpesa_consumer_secret
    environment = saved.get("environment") or settings.environment
    callback_url = saved.get("callback_url") or settings.mpesa_callback_url
    
    # Check if actually configured (not default values)
    is_configured = (
        consumer_key and 
        consumer_key != "YOUR_CONSUMER_KEY" and
        consumer_secret and 
        consumer_secret != "YOUR_CONSUMER_SECRET"
    )
    
    return MpesaCredentialsResponse(
        consumer_key_set=bool(consumer_key and consumer_key != "YOUR_CONSUMER_KEY"),
        consumer_secret_set=bool(consumer_secret and consumer_secret != "YOUR_CONSUMER_SECRET"),
        environment=environment,
        callback_url=callback_url,
        shortcode=settings.mpesa_shortcode,
        is_configured=is_configured,
        last_updated=saved.get("last_updated"),
    )


@router.post("/mpesa", response_model=MpesaCredentialsResponse)
async def save_mpesa_settings(credentials: MpesaCredentials):
    """
    Save M-Pesa credentials securely
    
    Only Consumer Key and Consumer Secret are required.
    Shortcode and Passkey use Safaricom sandbox defaults.
    """
    try:
        # Validate by testing connection
        logger.info(f"Saving M-Pesa credentials for {credentials.environment} environment")
        
        # Prepare credentials to save
        creds_to_save = {
            "consumer_key": credentials.consumer_key,
            "consumer_secret": credentials.consumer_secret,
            "environment": credentials.environment,
            "callback_url": credentials.callback_url or settings.mpesa_callback_url,
        }
        
        # Save to file
        _save_credentials(creds_to_save)
        
        # Reload M-Pesa service with new credentials
        mpesa_service.reload_credentials(
            consumer_key=credentials.consumer_key,
            consumer_secret=credentials.consumer_secret,
            environment=credentials.environment,
            callback_url=credentials.callback_url,
        )
        
        logger.info("M-Pesa credentials updated successfully")
        
        return MpesaCredentialsResponse(
            consumer_key_set=True,
            consumer_secret_set=True,
            environment=credentials.environment,
            callback_url=creds_to_save["callback_url"],
            shortcode=settings.mpesa_shortcode,
            is_configured=True,
            last_updated=datetime.utcnow().isoformat(),
        )
        
    except Exception as e:
        logger.error(f"Error saving credentials: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to save credentials: {str(e)}")


@router.post("/mpesa/test", response_model=TestConnectionResponse)
async def test_mpesa_connection():
    """
    Test M-Pesa API connection
    
    Attempts to get an OAuth access token to verify credentials are valid.
    """
    try:
        # Load current credentials
        saved = _load_credentials()
        consumer_key = saved.get("consumer_key") or settings.mpesa_consumer_key
        consumer_secret = saved.get("consumer_secret") or settings.mpesa_consumer_secret
        
        if not consumer_key or consumer_key == "YOUR_CONSUMER_KEY":
            return TestConnectionResponse(
                success=False,
                message="Consumer Key not configured. Please save your credentials first.",
                environment=settings.environment,
            )
        
        if not consumer_secret or consumer_secret == "YOUR_CONSUMER_SECRET":
            return TestConnectionResponse(
                success=False,
                message="Consumer Secret not configured. Please save your credentials first.",
                environment=settings.environment,
            )
        
        # Test by getting access token
        logger.info("Testing M-Pesa connection...")
        access_token = await mpesa_service.get_access_token()
        
        if access_token:
            logger.info("M-Pesa connection test successful")
            return TestConnectionResponse(
                success=True,
                message="Connection successful! API credentials are valid.",
                access_token_obtained=True,
                environment=mpesa_service.environment,
            )
        else:
            return TestConnectionResponse(
                success=False,
                message="Failed to obtain access token. Check your credentials.",
                environment=mpesa_service.environment,
            )
            
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Connection test failed: {error_msg}")
        
        # Provide helpful error messages
        if "401" in error_msg:
            message = "Invalid credentials. Please check your Consumer Key and Secret."
        elif "timeout" in error_msg.lower():
            message = "Connection timeout. Please check your network connection."
        else:
            message = f"Connection failed: {error_msg}"
        
        return TestConnectionResponse(
            success=False,
            message=message,
            environment=mpesa_service.environment,
        )


@router.delete("/mpesa")
async def clear_mpesa_settings():
    """
    Clear saved M-Pesa credentials
    """
    try:
        if CREDENTIALS_FILE.exists():
            os.remove(CREDENTIALS_FILE)
            logger.info("M-Pesa credentials cleared")
        
        # Reset service to default/env credentials
        mpesa_service.reload_credentials()
        
        return {"message": "Credentials cleared successfully"}
    except Exception as e:
        logger.error(f"Error clearing credentials: {e}")
        raise HTTPException(status_code=500, detail=str(e))

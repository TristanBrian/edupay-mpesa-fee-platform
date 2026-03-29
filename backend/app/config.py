"""
Application Configuration
Uses pydantic-settings for environment variable management
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    For M-Pesa Daraja API:
    - Get credentials from https://developer.safaricom.co.ke
    - Use sandbox credentials for testing
    - Callback URL must be publicly accessible (use ngrok for localhost)
    """
    
    # M-Pesa Daraja API Credentials
    mpesa_consumer_key: str = "YOUR_CONSUMER_KEY"
    mpesa_consumer_secret: str = "YOUR_CONSUMER_SECRET"
    mpesa_shortcode: str = "174379"  # Sandbox default
    mpesa_passkey: str = "bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919"  # Sandbox default
    
    # Callback URL - MUST be publicly accessible
    # For localhost: use ngrok (e.g., https://abc123.ngrok.io/api/v1/payments/callback)
    mpesa_callback_url: str = "https://your-domain.com/api/v1/payments/callback"
    
    # Database
    database_url: str = "sqlite+aiosqlite:///./edupay.db"
    
    # Environment: sandbox or production
    environment: str = "sandbox"
    
    # Debug mode
    debug: bool = True
    
    # Mock M-Pesa (for testing without actual API calls)
    # Set to False to use real M-Pesa API
    mock_mpesa: bool = True
    
    # API Configuration
    api_title: str = "EduPay API"
    api_version: str = "1.0.0"
    
    # CORS Origins (comma-separated for multiple)
    cors_origins: str = "*"
    
    # Rate Limiting
    rate_limit_calls: int = 100
    rate_limit_period: int = 60  # seconds

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False
    )


@lru_cache()
def get_settings() -> Settings:
    """
    Returns cached settings instance.
    Settings are loaded once and cached for performance.
    """
    return Settings()


# Usage instructions for developers
"""
SETUP INSTRUCTIONS:

1. Create a .env file in the backend directory:
   cp .env.example .env

2. Get Daraja API credentials:
   - Go to https://developer.safaricom.co.ke
   - Create an app and get Consumer Key/Secret
   - For testing, use Sandbox credentials

3. For localhost callback testing:
   - Install ngrok: https://ngrok.com
   - Run: ngrok http 8000
   - Use the HTTPS URL as your callback URL
   - Example: https://abc123.ngrok.io/api/v1/payments/callback

4. Update .env with your values:
   MPESA_CONSUMER_KEY=your_key
   MPESA_CONSUMER_SECRET=your_secret
   MPESA_CALLBACK_URL=https://your-ngrok-url/api/v1/payments/callback
   MOCK_MPESA=false  # Set to false to use real API

5. Run the server:
   cd backend
   uvicorn app.main:app --reload --port 8000
"""

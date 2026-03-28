from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    mpesa_consumer_key: str = "mock_key"
    mpesa_consumer_secret: str = "mock_secret"
    mpesa_shortcode: str = "174379"
    mpesa_passkey: str = "mock_passkey"
    mpesa_callback_url: str = "https://mock.com/callback"
    database_url: str = "sqlite+aiosqlite:///./flexifees.db"
    environment: str = "sandbox"
    debug: bool = True
    mock_mpesa: bool = True

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache()
def get_settings() -> Settings:
    return Settings()

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve .env from project root (parent of backend/)
_env_file = Path(__file__).resolve().parents[3] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_env_file) if _env_file.exists() else ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    debug: bool = False
    app_name: str = "Master CRM"

    # Database (owner role -- used by Alembic for migrations)
    database_url: str  # postgresql+asyncpg://mastercrm_owner:password@db:5432/mastercrm

    # Database (app role -- used by FastAPI at runtime for RLS enforcement)
    database_app_url: str  # postgresql+asyncpg://app_user:password@db:5432/mastercrm

    db_echo: bool = False

    # Auth
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Telegram
    tg_bot_token: str = ""
    tg_webhook_secret: str = ""
    mini_app_url: str = ""
    base_webhook_url: str = ""

    # MAX (VK Teams)
    max_bot_token: str = ""
    max_webhook_secret: str = ""  # X-Max-Bot-Api-Secret header value
    max_bot_username: str = ""  # For deep link generation

    # VK
    vk_group_token: str = ""  # Community bot access token
    vk_app_id: str = ""  # VK Mini App application ID
    vk_app_secret: str = ""  # VK Mini App secret key (for sign validation)
    vk_confirmation_token: str = ""  # VK Callback API confirmation string
    vk_secret_key: str = ""  # VK Callback API secret key

    # Web admin panel
    web_admin_url: str = "http://localhost:3001/admin"  # Base URL for magic link generation

    # CORS
    allowed_origins: list[str] = ["http://localhost:3000"]

    # Encryption (for Robokassa credentials)
    encryption_key: str = ""  # Fernet key, generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

    # Robokassa
    robokassa_result_url: str = ""  # e.g. https://yourdomain.com/webhook/robokassa/result


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

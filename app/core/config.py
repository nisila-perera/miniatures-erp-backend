"""Application configuration settings"""
import json
from typing import Annotated, List

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, NoDecode


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@db:5432/miniatures_erp"
    
    # CORS
    CORS_ORIGINS: Annotated[List[str], NoDecode] = Field(
        default=["http://localhost:3000", "http://frontend:3000"],
        validation_alias=AliasChoices("CORS_ORIGINS", "ALLOWED_ORIGINS"),
    )
    CORS_ORIGIN_REGEX: str = ""
    
    # WooCommerce
    WOOCOMMERCE_URL: str = ""
    WOOCOMMERCE_CONSUMER_KEY: str = ""
    WOOCOMMERCE_CONSUMER_SECRET: str = ""
    
    # Email
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = ""
    
    # File Upload
    MAX_UPLOAD_SIZE: int = 5 * 1024 * 1024  # 5MB
    UPLOAD_DIR: str = "/app/uploads"
    
    # Brand Colors
    BRAND_COLOR_PRIMARY: str = "#C9A66B"
    BRAND_COLOR_SECONDARY: str = "#EBD3A0"
    BRAND_COLOR_DARK: str = "#2F2F2F"

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, value):
        """Accept both JSON array and comma-separated env values."""
        if isinstance(value, str):
            raw_value = value.strip()
            if not raw_value:
                return []
            if raw_value.startswith("["):
                try:
                    value = json.loads(raw_value)
                except json.JSONDecodeError:
                    pass
            else:
                value = [origin.strip() for origin in raw_value.split(",")]

        if isinstance(value, list):
            return [str(origin).strip().rstrip("/") for origin in value if str(origin).strip()]

        return value
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

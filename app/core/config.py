"""Application configuration settings"""
import json
from typing import List

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@db:5432/miniatures_erp"
    
    # CORS
    CORS_ORIGINS: str = Field(
        default="http://localhost:3000,http://frontend:3000",
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

    def get_cors_origins(self) -> List[str]:
        """Accept both JSON array and comma-separated env values."""
        raw_value = (self.CORS_ORIGINS or "").strip()
        if not raw_value:
            return []
        if raw_value.startswith("["):
            try:
                parsed = json.loads(raw_value)
            except json.JSONDecodeError:
                parsed = []
            if isinstance(parsed, list):
                return [str(origin).strip().rstrip("/") for origin in parsed if str(origin).strip()]
        return [origin.strip().rstrip("/") for origin in raw_value.split(",") if origin.strip()]
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


settings = Settings()

"""Application configuration settings"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@db:5432/miniatures_erp"
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://frontend:3000"]
    
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
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

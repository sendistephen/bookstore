import os
import secrets
from typing import Dict, Type
from dotenv import load_dotenv
from datetime import timedelta

load_dotenv()


class Config:
    """Base configuration for the application."""

    # Flask settings
    SECRET_KEY: str = os.environ.get("SECRET_KEY") or secrets.token_hex(32)

    # Database settings
    POSTGRES_USER: str = os.environ.get('POSTGRES_USER')
    POSTGRES_PASSWORD: str = os.environ.get('POSTGRES_PASSWORD')
    POSTGRES_DB: str = os.environ.get('POSTGRES_DB')
    POSTGRES_PORT: str = os.environ.get('POSTGRES_PORT')

    # SQLAlchemy settings
    SQLALCHEMY_DATABASE_URI: str = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@postgres_db:{POSTGRES_PORT}/{POSTGRES_DB}"
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False

    # API settings
    API_VERSION: str = "v1"
    API_PREFIX: str = f"/api/{API_VERSION}"
    API_HOST: str = os.environ.get("API_HOST", "http://localhost:8080")

    # JWT settings
    JWT_SECRET_KEY: str = os.environ.get("JWT_SECRET_KEY") or secrets.token_hex(32)
    JWT_ACCESS_TOKEN_EXPIRES: timedelta = timedelta(days=30)
    JWT_REFRESH_TOKEN_EXPIRES: timedelta = timedelta(days=7)

    # CORS settings
    CORS_ORIGIN: list = ["http://localhost:3000"]

    # Email settings
    MAIL_SERVER: str = os.environ.get("MAIL_SERVER", "mailhog")
    MAIL_PORT: int = int(os.environ.get("MAIL_PORT", 1025))
    MAIL_USE_TLS: bool = os.environ.get("MAIL_USE_TLS", "False").lower() == "true"
    MAIL_USE_SSL: bool = os.environ.get("MAIL_USE_SSL", "False").lower() == "true"
    MAIL_USERNAME: str = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD: str = os.environ.get("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER: str = os.environ.get("MAIL_DEFAULT_SENDER", "noreply@bookstore.com")
    MAIL_MAX_EMAILS: int = int(os.environ.get("MAIL_MAX_EMAILS", 100))
    MAIL_ASCII_ATTACHMENTS: bool = True

    # Email verification settings
    VERIFY_EMAIL_TOKEN_EXPIRY: timedelta = timedelta(hours=24)

    # Redis and Session settings
    REDIS_HOST: str = os.environ.get('REDIS_HOST', 'redis')
    REDIS_PORT: int = int(os.environ.get('REDIS_PORT', 6379))
    REDIS_DB: int = int(os.environ.get('REDIS_DB', 0))
    REDIS_URL: str = os.environ.get('REDIS_URL', f'redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}')
    
    # Session configuration
    SESSION_TYPE: str = 'redis'
    SESSION_PERMANENT: bool = True
    PERMANENT_SESSION_LIFETIME: timedelta = timedelta(minutes=30)
    SESSION_USE_SIGNER: bool = True
    SESSION_KEY_PREFIX: str = 'bookstore:'
    SESSION_COOKIE_SECURE: bool = False  # Set to True in production
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SAMESITE: str = 'Lax'
    SESSION_REFRESH_EACH_REQUEST: bool = True


class DevelopmentConfig(Config):
    """Development configuration for the application."""
    DEBUG: bool = True
    DEVELOPMENT: bool = True
    MAIL_DEBUG: bool = True
    
    SQL_ALCHEMY_ECHO: bool = True


class ProductionConfig(Config):
    """Production configuration for the application."""
    DEBUG: bool = False
    MAIL_SERVER: str = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT: int = int(os.environ.get("MAIL_PORT", 587))
    MAIL_USE_TLS: bool = True
    MAIL_USE_SSL: bool = False
    MAIL_USERNAME: str = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD: str = os.environ.get("MAIL_PASSWORD")
    CONTACT_URL: str = os.environ.get("CONTACT_URL", "https://bookstore.com/contact")
    SESSION_COOKIE_SECURE: bool = True  # Force HTTPS in production


class TestingConfig(Config):
    """Testing configuration for the application."""
    TESTING: bool = True
    SQLALCHEMY_DATABASE_URI: str = "sqlite:///memory.db"
    MAIL_SUPPRESS_SEND: bool = True
    WTF_CSRF_ENABLED: bool = False
    SESSION_TYPE: str = 'filesystem'  # Use filesystem sessions in testing


config: Dict[str, Type[Config]] = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig
}

import os
from dotenv import load_dotenv
from datetime import timedelta

load_dotenv()


class Config:
    """Base configuration for the application."""

    # flask settings
    SECRET_KEY = os.environ.get("SECRET_KEY") or "my_precious_secret_key"

    # SQLAlchemy settings
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # API settings
    API_VERSION = "v1"
    API_PREFIX = f"/api/{API_VERSION}"
    API_HOST = os.environ.get("API_HOST")

    # JWT settings
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=7)

    # CORS settings
    CORS_ORIGIN = ["http://localhost:3000"]


class DevelopmentConfig(Config):
    """Development configuration for the application."""
    DEBUG = True
    DEVELOPMENT = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DEV_DATABASE_URI") or "sqlite:///development.db"


class ProductionConfig(Config):
    """Production configuration for the application."""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URI") or "sqlite:///production.db"


class TestingConfig(Config):
    """Testing configuration for the application."""
    TESTING = True
    DATABASE_URI = "sqlite:///memory.db"


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig
}

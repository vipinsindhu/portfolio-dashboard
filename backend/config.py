"""
Configuration management for different environments
Supports local development, testing, and production
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class Config:
    """Base configuration for all environments"""

    # Flask
    DEBUG: bool = False
    TESTING: bool = False
    FLASK_ENV: str = "production"

    # Database
    DATABASE_URL: str = "sqlite:///portfolio.db"  # Local default
    DATABASE_POOL_SIZE: int = 10
    DATABASE_POOL_RECYCLE: int = 3600
    DATABASE_ECHO: bool = False

    # Redis (optional, for Phase 3)
    REDIS_URL: Optional[str] = None

    # API
    ANTHROPIC_API_KEY: str = ""
    MAX_WORKERS: int = 4
    REQUEST_TIMEOUT: int = 120

    # CORS
    CORS_ORIGINS: str = "*"

    # Storage (backwards compat for signals.json)
    SIGNALS_FILE: str = "signals.json"
    MACRO_CONFIG_FILE: str = "macro_config.json"

    @classmethod
    def from_env(cls):
        """Load configuration from environment variables"""
        return cls(
            DEBUG=os.getenv("DEBUG", "false").lower() == "true",
            TESTING=os.getenv("TESTING", "false").lower() == "true",
            FLASK_ENV=os.getenv("FLASK_ENV", "production"),
            DATABASE_URL=os.getenv("DATABASE_URL", "sqlite:///portfolio.db"),
            DATABASE_POOL_SIZE=int(os.getenv("DATABASE_POOL_SIZE", "10")),
            DATABASE_POOL_RECYCLE=int(os.getenv("DATABASE_POOL_RECYCLE", "3600")),
            DATABASE_ECHO=os.getenv("DATABASE_ECHO", "false").lower() == "true",
            REDIS_URL=os.getenv("REDIS_URL"),
            ANTHROPIC_API_KEY=os.getenv("ANTHROPIC_API_KEY", ""),
            MAX_WORKERS=int(os.getenv("MAX_WORKERS", "4")),
            REQUEST_TIMEOUT=int(os.getenv("REQUEST_TIMEOUT", "120")),
            CORS_ORIGINS=os.getenv("CORS_ORIGINS", "*"),
            SIGNALS_FILE=os.getenv("SIGNALS_FILE", "signals.json"),
            MACRO_CONFIG_FILE=os.getenv("MACRO_CONFIG_FILE", "macro_config.json"),
        )


class DevelopmentConfig(Config):
    """Development environment configuration"""
    DEBUG = True
    FLASK_ENV = "development"
    DATABASE_ECHO = True
    CORS_ORIGINS = "http://localhost:5173,http://localhost:5180"


class TestingConfig(Config):
    """Testing environment configuration"""
    TESTING = True
    FLASK_ENV = "testing"
    DATABASE_URL = "sqlite:///:memory:"  # Use in-memory database for tests
    CORS_ORIGINS = "http://localhost:5173"


class ProductionConfig(Config):
    """Production environment configuration"""
    DEBUG = False
    FLASK_ENV = "production"
    # DATABASE_URL should be set via environment variable
    # Example: "mssql+pyodbc://user:pass@server.database.windows.net/dbname?driver=ODBC+Driver+17+for+SQL+Server"


def get_config():
    """Get configuration based on environment"""
    env = os.getenv("FLASK_ENV", "production").lower()

    if env == "development":
        return DevelopmentConfig.from_env()
    elif env == "testing":
        return TestingConfig.from_env()
    else:
        return ProductionConfig.from_env()

"""
Environment and configuration management for multi-environment support
Supports production (https://letsplaydarts.eu) and development (http://dev.letsplaydarts.eu)
"""

import os
from typing import Literal

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Base configuration class"""

    ENVIRONMENT = os.getenv("ENVIRONMENT", "production").lower()
    APP_DOMAIN = os.getenv("APP_DOMAIN", "localhost:5000")
    APP_SCHEME = os.getenv("APP_SCHEME", "https")

    # Derived URLs
    APP_URL = f"{APP_SCHEME}://{APP_DOMAIN}"
    CALLBACK_URL = f"{APP_URL}/callback"
    LOGOUT_REDIRECT_URL = f"{APP_URL}/"

    # Swagger configuration
    SWAGGER_HOST = os.getenv("SWAGGER_HOST", APP_DOMAIN)

    # SSL/Session configuration
    FLASK_USE_SSL = os.getenv("FLASK_USE_SSL", "true").lower() == "true"
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "").lower() == "true"

    # If SESSION_COOKIE_SECURE not explicitly set, derive from scheme
    if not os.getenv("SESSION_COOKIE_SECURE"):
        SESSION_COOKIE_SECURE = APP_SCHEME == "https" or FLASK_USE_SSL

    @classmethod
    def get_environment(cls) -> Literal["production", "development", "staging"]:
        """Get current environment"""
        return cls.ENVIRONMENT  # type: ignore

    @classmethod
    def is_production(cls) -> bool:
        """Check if running in production"""
        return cls.ENVIRONMENT == "production"

    @classmethod
    def is_development(cls) -> bool:
        """Check if running in development"""
        return cls.ENVIRONMENT == "development"

    @classmethod
    def get_app_url(cls, path: str = "") -> str:
        """Get full app URL with optional path"""
        url = cls.APP_URL
        if path:
            if not path.startswith("/"):
                path = "/" + path
            url += path
        return url

    @classmethod
    def __repr__(cls) -> str:
        """Return string representation of Config."""
        return (
            f"Config(environment={cls.ENVIRONMENT}, "
            f"domain={cls.APP_DOMAIN}, scheme={cls.APP_SCHEME})"
        )


# Export configuration
__all__ = ["Config"]

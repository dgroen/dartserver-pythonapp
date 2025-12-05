"""
Dartserver Core - Authentication, Configuration, and Database Module

Provides core functionality for the Darts Game application including:
- OAuth2/OIDC authentication with WSO2 Identity Server
- Role-based access control (RBAC)
- Database models and operations
- Application configuration
"""

from dartserver_core.auth import (
    exchange_code_for_token,
    get_authorization_url,
    get_dynamic_post_logout_redirect_uri,
    get_dynamic_redirect_uri,
    get_user_info,
    login_required,
    logout_user,
    permission_required,
    role_required,
)
from dartserver_core.config import Config
from dartserver_core.database_models import (
    ApiKey,
    Dartboard,
    DartboardType,
    DartboardZoneMapping,
    GameResult,
    GameType,
    HotspotConfig,
    Player,
)
from dartserver_core.database_service import (
    get_session,
    set_database_service,
)

__version__ = "1.0.0"
__all__ = [
    "Config",
    "get_session",
    "set_database_service",
    "login_required",
    "role_required",
    "permission_required",
    "logout_user",
    "get_authorization_url",
    "exchange_code_for_token",
    "get_user_info",
    "get_dynamic_redirect_uri",
    "get_dynamic_post_logout_redirect_uri",
    "Player",
    "GameResult",
    "GameType",
    "ApiKey",
    "Dartboard",
    "HotspotConfig",
    "DartboardType",
    "DartboardZoneMapping",
]

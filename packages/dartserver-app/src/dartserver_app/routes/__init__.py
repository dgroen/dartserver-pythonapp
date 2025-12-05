"""Route registration module with blueprint organization."""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


ROUTE_DOMAINS = {
    "auth": {
        "description": "Authentication routes",
        "count": 6,
        "routes": ["/login", "/callback", "/logout", "/profile", "/debug/auth", "/test-refresh"],
    },
    "ui": {
        "description": "User interface routes",
        "count": 15,
        "routes": [
            "/",
            "/service-worker.js",
            "/health",
            "/control",
            "/history",
            "/dashboard",
            "/training",
            "/training/dashboard",
            "/mobile",
            "/mobile/gameplay",
            "/mobile/gamemaster",
            "/mobile/dartboard-setup",
            "/mobile/results",
            "/mobile/account",
            "/mobile/hotspot",
            "/admin/dartboard-testing",
        ],
    },
    "game": {
        "description": "Game management API",
        "count": 13,
        "routes": [
            "/api/game/state",
            "/api/game/new",
            "/api/game/start",
            "/api/game/end",
            "/api/game/current",
            "/api/game/current/session_id",
            "/api/game/types",
            "/api/game/results",
            "/api/game/<game_session_id>",
            "/api/game/resume/<game_session_id>",
            "/api/game/history",
            "/api/game/replay/<game_session_id>",
            "/api/active-games",
        ],
    },
    "player": {
        "description": "Player management API",
        "count": 6,
        "routes": [
            "/api/players",
            "/api/players/<int:player_id>",
            "/api/user/current",
            "/api/wso2/users/search",
            "/api/player/history",
            "/api/player/statistics",
        ],
    },
    "score": {
        "description": "Score submission API",
        "count": 1,
        "routes": ["/api/Throw/zone"],
    },
    "dartboard": {
        "description": "Dartboard management API",
        "count": 7,
        "routes": [
            "/api/dartboard/types",
            "/api/dartboard/types/<board_type>/mappings",
            "/api/dartboard/connect",
            "/api/dartboard/score",
            "/api/admin/dartboard/matrix/<board_type>",
            "/api/admin/dartboard/mapping",
            "/api/admin/dartboard/import",
        ],
    },
    "tts": {
        "description": "Text-to-Speech API",
        "count": 6,
        "routes": [
            "/api/tts/config",
            "/api/tts/voices",
            "/api/tts/languages",
            "/api/tts/test",
            "/api/tts/generate",
            "/api/admin/tts/player",
        ],
    },
    "mobile": {
        "description": "Mobile API",
        "count": 7,
        "routes": [
            "/api/mobile/apikeys",
            "/api/mobile/apikeys/<int:key_id>",
            "/api/mobile/dartboards",
            "/api/mobile/dartboards/<int:dartboard_id>",
            "/api/mobile/hotspot",
            "/api/mobile/hotspot/<int:config_id>/toggle",
            "/api/mobile/game/start-single-player",
        ],
    },
    "training": {
        "description": "Training mode API",
        "count": 4,
        "routes": [
            "/api/training/start",
            "/api/training/end",
            "/api/training/history",
            "/api/training/statistics",
        ],
    },
    "debug": {
        "description": "Debug and utility routes",
        "count": 1,
        "routes": ["/api/debug/session"],
    },
}

SOCKETIO_EVENTS = [
    "connect",
    "disconnect",
    "new_game",
    "add_player",
    "remove_player",
    "next_player",
    "skip_to_player",
    "end_turn_early",
    "manual_score",
    "set_throwout_advice",
    "dartboard_test_message",
]


def get_routes_summary() -> dict:
    """Get summary of all routes."""
    total = sum(info["count"] for info in ROUTE_DOMAINS.values())
    return {"total_routes": total, "domains": len(ROUTE_DOMAINS), "events": len(SOCKETIO_EVENTS)}


def get_domain_info(domain: str) -> Optional[dict]:
    """Get info for a specific domain."""
    return ROUTE_DOMAINS.get(domain)


def get_all_domains() -> dict:
    """Get all domain information."""
    return ROUTE_DOMAINS


def get_domain_for_route(route_path: str) -> Optional[str]:
    """Determine which domain a route belongs to."""
    for domain, info in ROUTE_DOMAINS.items():
        if route_path in info["routes"]:
            return domain
    return None


def register_routes(app):
    """
    Register all routes with the Flask app.

    Routes are currently defined in src/app/app.py.
    This function validates route organization and can be extended to
    register blueprints as routes are incrementally extracted.

    Args:
        app: Flask application instance
    """
    summary = get_routes_summary()
    logger.info(
        f"Route registry loaded: {summary['total_routes']} routes across \
            {summary['domains']} domains"
    )

    for domain, info in ROUTE_DOMAINS.items():
        logger.debug(f"  {domain}: {info['count']} routes ({info['description']})")


__all__ = [
    "register_routes",
    "get_routes_summary",
    "get_domain_info",
    "get_all_domains",
    "get_domain_for_route",
    "ROUTE_DOMAINS",
    "SOCKETIO_EVENTS",
]

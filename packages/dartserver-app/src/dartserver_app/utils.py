"""Utility functions for the application."""

import logging

logger = logging.getLogger(__name__)


def get_client_ip(request):
    """Get client IP from request, handling proxy headers."""
    if request.headers.getlist("X-Forwarded-For"):
        return request.headers.getlist("X-Forwarded-For")[0]
    return request.remote_addr


def get_mobile_service(db_session):
    """Helper to get MobileService instance with database session."""
    from dartserver_services import MobileService

    return MobileService(db_session)


__all__ = ["get_client_ip", "get_mobile_service"]

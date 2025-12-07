"""Compatibility shim to expose core database models for tests.

This module re-exports symbols from dartserver_core.database_models so tests
that import `database_models` can still resolve them.
"""

from dartserver_core.database_models import *  # noqa: F403

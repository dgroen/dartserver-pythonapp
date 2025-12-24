"""Compatibility shim - imports from dartserver_core.

This module mirrors attributes to ``dartserver_core.auth`` so that tests
patching ``src.core.auth`` also affect the underlying implementation used by
decorators.
"""

import dartserver_core.auth as _core_auth
from dartserver_core.auth import *  # noqa: F403


def __getattr__(name):
    if name in globals():
        return globals()[name]
    return getattr(_core_auth, name)


def __setattr__(name, value):  # noqa: N807
    globals()[name] = value
    if hasattr(_core_auth, name):
        setattr(_core_auth, name, value)


# Provide test-friendly defaults for values tests expect to patch
# Tests patch `src.core.auth.AUTH_DISABLED` — ensure it exists here and
# mirror it into the underlying implementation if absent.
if not hasattr(_core_auth, "AUTH_DISABLED"):
    AUTH_DISABLED = False
    _core_auth.AUTH_DISABLED = AUTH_DISABLED
else:
    AUTH_DISABLED = _core_auth.AUTH_DISABLED

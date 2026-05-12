"""Compatibility shim - imports from dartserver_app.

This file is a thin shim used by the application entrypoints. During
development the `dartserver_app` package lives under
`packages/dartserver-app/src` so it may not be on `sys.path` unless the
package was installed in editable mode. Try a normal import first and
fall back to adding the local package `src` path to `sys.path`.
"""

try:
    from dartserver_app.multi_game_manager import *  # noqa: F403
except Exception:  # pragma: no cover - runtime fallback for dev environments
    import importlib
    import os
    import sys

    # Determine repository root from this file (src/app/...)
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    package_src = os.path.join(repo_root, "packages", "dartserver-app", "src")

    if os.path.isdir(package_src) and package_src not in sys.path:
        sys.path.insert(0, package_src)

    try:
        mod = importlib.import_module("dartserver_app.multi_game_manager")
    except Exception:
        # As a last resort load the module directly from the package file path
        import importlib.util

        module_file = os.path.join(package_src, "dartserver_app", "multi_game_manager.py")
        if os.path.isfile(module_file):
            spec = importlib.util.spec_from_file_location(
                "dartserver_app.multi_game_manager",
                module_file,
            )
            mod = importlib.util.module_from_spec(spec)  # type: ignore
            spec.loader.exec_module(mod)  # type: ignore
        else:
            raise

    for name in dir(mod):
        if not name.startswith("_"):
            globals()[name] = getattr(mod, name)

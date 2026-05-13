"""Unit tests for WSO2 test client registration helper."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace


def _load_module(monkeypatch, **env):
    """Load the helper module with a controlled environment."""
    defaults = {
        "WSO2_DCR_AUTH_MODE": "auto",
        "WSO2_DCR_BEARER_TOKEN": "",
        "WSO2_ADMIN_USER": "",
        "WSO2_ADMIN_PASS": "",
        "WSO2_ADMIN_USERNAME": "",
        "WSO2_ADMIN_PASSWORD": "",
        "WSO2_IS_INTROSPECT_USER": "",
        "WSO2_IS_INTROSPECT_PASSWORD": "",
    }
    defaults.update(env)
    for key, value in defaults.items():
        monkeypatch.setenv(key, value)

    module_path = (
        Path(__file__).resolve().parents[2] / "helpers" / "register_wso2_test_client.py"
    )
    spec = importlib.util.spec_from_file_location("register_wso2_test_client", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_admin_username_password_fallback(monkeypatch):
    """Script should honor WSO2_ADMIN_USERNAME/WSO2_ADMIN_PASSWORD."""
    module = _load_module(
        monkeypatch,
        WSO2_ADMIN_USERNAME="fallback-user",
        WSO2_ADMIN_PASSWORD="fallback-pass",
    )

    assert module.WSO2_ADMIN_USER == "fallback-user"
    assert module.WSO2_ADMIN_PASS == "fallback-pass"


def test_dcr_request_retries_with_bearer_on_401(monkeypatch):
    """Auto mode should retry with bearer token after basic-auth 401."""
    module = _load_module(monkeypatch, WSO2_DCR_BEARER_TOKEN="token-123")

    calls = []

    def fake_request(method, url, **kwargs):
        calls.append({"method": method, "url": url, **kwargs})
        if len(calls) == 1:
            return SimpleNamespace(status_code=401, text="unauthorized")
        return SimpleNamespace(status_code=200, text="ok")

    monkeypatch.setattr(module.requests, "request", fake_request)

    response = module._dcr_request("GET", "https://example.test/dcr")

    assert response.status_code == 200
    assert len(calls) == 2
    assert calls[0]["auth"] == (module.WSO2_ADMIN_USER, module.WSO2_ADMIN_PASS)
    assert "Authorization" not in calls[0]["headers"]
    assert calls[1].get("auth") is None
    assert calls[1]["headers"]["Authorization"] == "Bearer token-123"


def test_dcr_request_uses_bearer_mode_without_basic_auth(monkeypatch):
    """Bearer mode should use only Authorization header from first call."""
    module = _load_module(
        monkeypatch,
        WSO2_DCR_AUTH_MODE="bearer",
        WSO2_DCR_BEARER_TOKEN="token-456",
    )

    calls = []

    def fake_request(method, url, **kwargs):
        calls.append({"method": method, "url": url, **kwargs})
        return SimpleNamespace(status_code=200, text="ok")

    monkeypatch.setattr(module.requests, "request", fake_request)

    response = module._dcr_request("POST", "https://example.test/dcr", json_payload={"x": 1})

    assert response.status_code == 200
    assert len(calls) == 1
    assert calls[0].get("auth") is None
    assert calls[0]["headers"]["Authorization"] == "Bearer token-456"
    assert calls[0]["headers"]["Content-Type"] == "application/json"

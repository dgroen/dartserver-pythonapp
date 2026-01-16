import types

from dartserver_core import auth


class DummyResponse:
    def __init__(self, status_code=200, payload=None, text=""):
        self.status_code = status_code
        self._payload = payload or {}
        self.text = text or ""

    def json(self):
        return self._payload


def test_search_uses_basic_auth_when_no_token(monkeypatch):
    captured = {}

    def fake_get(url, params=None, headers=None, auth=None, verify=None, timeout=None):
        captured.update(
            {
                "url": url,
                "params": params,
                "headers": headers or {},
                "auth": auth,
                "verify": verify,
                "timeout": timeout,
            },
        )
        payload = {
            "Resources": [
                {
                    "id": "1",
                    "userName": "alice",
                    "emails": [{"value": "a@example.com"}],
                    "name": {"givenName": "Alice", "familyName": "Anderson"},
                },
            ],
        }
        return DummyResponse(200, payload)

    monkeypatch.setattr(auth, "WSO2_IS_INTROSPECT_USER", "admin")
    monkeypatch.setattr(auth, "WSO2_IS_INTROSPECT_PASSWORD", "pass")
    monkeypatch.setattr(auth, "WSO2_IS_INTERNAL_URL", "https://idp")
    monkeypatch.setattr(auth, "requests", types.SimpleNamespace(get=fake_get))

    users = auth.search_wso2_users("alice")

    assert captured["auth"] == ("admin", "pass")
    assert "Authorization" not in captured["headers"]
    assert captured["headers"].get("Content-Type") == "application/scim+json"
    # Filter should be present when query is non-empty
    assert "filter" in captured["params"]
    assert captured["params"]["filter"] == 'userName co "alice"'
    assert any(user["username"] == "alice" for user in users)


def test_load_all_users_no_filter(monkeypatch):
    """Test that loading all users (empty query) doesn't include a filter"""
    captured = {}

    def fake_get(url, params=None, headers=None, auth=None, verify=None, timeout=None):
        captured.update({"params": params or {}})
        return DummyResponse(200, {"Resources": []})

    monkeypatch.setattr(auth, "WSO2_IS_INTROSPECT_USER", "admin")
    monkeypatch.setattr(auth, "WSO2_IS_INTROSPECT_PASSWORD", "pass")
    monkeypatch.setattr(auth, "WSO2_IS_INTERNAL_URL", "https://idp")
    monkeypatch.setattr(auth, "requests", types.SimpleNamespace(get=fake_get))

    auth.search_wso2_users("")  # Empty query = load all

    # Empty query should NOT send a filter param
    assert "filter" not in captured["params"]
    assert captured["params"].get("count") == "100"


def test_search_uses_bearer_when_token_present(monkeypatch):
    captured = {}

    def fake_get(url, params=None, headers=None, auth=None, verify=None, timeout=None):
        captured.update({"headers": headers or {}, "auth": auth})
        return DummyResponse(200, {"Resources": []})

    monkeypatch.setattr(auth, "WSO2_IS_INTERNAL_URL", "https://idp")
    monkeypatch.setattr(auth, "WSO2_IS_VERIFY_SSL", False)
    monkeypatch.setattr(auth, "requests", types.SimpleNamespace(get=fake_get))

    auth.search_wso2_users("bob", access_token="token123")

    assert captured["auth"] is None
    assert captured["headers"].get("Authorization") == "Bearer token123"
    assert captured["headers"].get("Content-Type") == "application/scim+json"


def test_get_user_info_basic_auth_when_no_token(monkeypatch):
    captured = {}

    def fake_get(url, params=None, headers=None, auth=None, verify=None, timeout=None):
        captured.update({"headers": headers or {}, "auth": auth})
        payload = {
            "Resources": [
                {
                    "id": "2",
                    "userName": "bob",
                    "emails": ["b@example.com"],
                    "name": {"givenName": "Bob", "familyName": "Bishop"},
                },
            ],
        }
        return DummyResponse(200, payload)

    monkeypatch.setattr(auth, "WSO2_IS_INTERNAL_URL", "https://idp")
    monkeypatch.setattr(auth, "WSO2_IS_INTROSPECT_USER", "admin")
    monkeypatch.setattr(auth, "WSO2_IS_INTROSPECT_PASSWORD", "pass")
    monkeypatch.setattr(auth, "requests", types.SimpleNamespace(get=fake_get))

    user = auth.get_wso2_user_info("bob")

    assert captured["auth"] == ("admin", "pass")
    assert "Authorization" not in captured["headers"]
    assert user["username"] == "bob"
    assert user["email"] == "b@example.com"
    assert user["name"] == "Bob Bishop"

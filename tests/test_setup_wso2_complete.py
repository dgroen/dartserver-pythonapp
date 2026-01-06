"""
Tests for WSO2 complete setup orchestrator
"""

from unittest.mock import Mock, patch

import pytest

import helpers.setup_wso2_complete
from helpers.setup_wso2_complete import WSO2SetupOrchestrator


@pytest.fixture
def mock_env(tmp_path, monkeypatch):
    """Create temporary .env file for testing."""
    # Unset real environment variables
    monkeypatch.delenv("WSO2_IS_URL", raising=False)
    monkeypatch.delenv("WSO2_ADMIN_USERNAME", raising=False)
    monkeypatch.delenv("WSO2_ADMIN_PASSWORD", raising=False)

    env_file = tmp_path / ".env"
    env_file.write_text(
        """WSO2_IS_URL=https://test.example.com:9443
WSO2_ADMIN_USERNAME=testadmin
WSO2_ADMIN_PASSWORD=testpass
WSO2_CLIENT_ID=test_client_id
WSO2_REDIRECT_URI=https://test.example.com/callback
WSO2_POST_LOGOUT_REDIRECT_URI=https://test.example.com/
""",
    )
    return env_file


@pytest.fixture
def orchestrator(mock_env, monkeypatch):
    """Create orchestrator instance with test environment."""
    # Prevent loading real .env by making load_dotenv a no-op for this test
    monkeypatch.setattr(
        helpers.setup_wso2_complete,
        "load_dotenv",
        lambda *_args, **_kwargs: None,
    )

    # Set environment variables manually
    monkeypatch.setenv("WSO2_IS_URL", "https://test.example.com:9443")
    monkeypatch.setenv("WSO2_ADMIN_USERNAME", "testadmin")
    monkeypatch.setenv("WSO2_ADMIN_PASSWORD", "testpass")
    monkeypatch.setenv("WSO2_CLIENT_ID", "test_client_id")

    return WSO2SetupOrchestrator(env_file=str(mock_env), environment="test")


def test_orchestrator_initialization(orchestrator):
    """Test orchestrator initializes with correct configuration."""
    assert orchestrator.environment == "test"
    assert orchestrator.wso2_url == "https://test.example.com:9443"
    assert orchestrator.wso2_admin_user == "testadmin"
    assert orchestrator.wso2_admin_password == "testpass"
    assert orchestrator.client_id == "test_client_id"


def test_resolve_env_file_development():
    """Test environment file resolution for development."""
    orchestrator = WSO2SetupOrchestrator(environment="development")
    assert orchestrator.env_file.name == ".env"


def test_resolve_env_file_test(tmp_path):
    """Test environment file resolution for test."""
    test_env = tmp_path / ".env.test"
    test_env.write_text("TEST=true")

    with patch("helpers.setup_wso2_complete.Path") as mock_path:
        mock_path.return_value.parent = tmp_path
        WSO2SetupOrchestrator(environment="test")
        # Will fallback to .env if .env.test doesn't exist in real location


@patch("helpers.setup_wso2_complete.requests.get")
def test_wait_for_wso2_ready_success(mock_get, orchestrator):
    """Test waiting for WSO2 when it becomes ready."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_get.return_value = mock_response

    result = orchestrator.wait_for_wso2_ready(max_retries=3, retry_delay=0)

    assert result is True
    mock_get.assert_called()


@patch("helpers.setup_wso2_complete.requests.get")
@patch("helpers.setup_wso2_complete.time.sleep")
def test_wait_for_wso2_ready_timeout(mock_sleep, mock_get, orchestrator):
    """Test waiting for WSO2 times out."""
    import requests  # noqa: PLC0415

    mock_get.side_effect = requests.exceptions.ConnectionError("Connection refused")

    result = orchestrator.wait_for_wso2_ready(max_retries=2, retry_delay=0)

    assert result is False
    # Should make exactly max_retries attempts
    assert mock_get.call_count == 2


@patch("helpers.setup_wso2_complete.subprocess.run")
def test_run_script_success(mock_run, orchestrator, tmp_path):
    """Test running a helper script successfully."""
    # Create fake script
    script = tmp_path / "test_script.py"
    script.write_text("#!/usr/bin/env python3\nprint('success')")

    mock_run.return_value = Mock(returncode=0)

    with patch.object(orchestrator, "helpers_dir", tmp_path):
        result = orchestrator.run_script("test_script.py", "Test script")

    assert result is True
    mock_run.assert_called_once()


@patch("helpers.setup_wso2_complete.subprocess.run")
def test_run_script_failure(mock_run, orchestrator, tmp_path):
    """Test running a helper script that fails."""
    script = tmp_path / "test_script.py"
    script.write_text("#!/usr/bin/env python3\nexit(1)")

    mock_run.return_value = Mock(returncode=1)

    with patch.object(orchestrator, "helpers_dir", tmp_path):
        result = orchestrator.run_script("test_script.py", "Test script")

    assert result is False


def test_run_script_not_found(orchestrator):
    """Test running a script that doesn't exist."""
    result = orchestrator.run_script("nonexistent_script.py", "Test script")
    assert result is False


@patch("helpers.setup_wso2_complete.requests.get")
def test_validate_setup_success(mock_get, orchestrator):
    """Test validation passes when all checks succeed."""
    # Mock successful responses
    login_response = Mock()
    login_response.status_code = 200

    apps_response = Mock()
    apps_response.status_code = 200
    apps_response.json.return_value = {
        "applications": [
            {"name": "DartsApp", "id": "dart-123"},
            {"name": "APIM_KeyManager", "id": "apim-km"},
            {"name": "APIM_Publisher", "id": "apim-pub"},
            {"name": "APIM_DevPortal", "id": "apim-dev"},
            {"name": "APIM_Admin", "id": "apim-admin"},
        ],
    }

    mock_get.side_effect = [login_response, apps_response, apps_response]

    result = orchestrator.validate_setup()
    assert result is True


@patch("helpers.setup_wso2_complete.requests.get")
def test_validate_setup_missing_darts_app(mock_get, orchestrator):
    """Test validation fails when DartsApp is missing."""
    login_response = Mock()
    login_response.status_code = 200

    apps_response = Mock()
    apps_response.status_code = 200
    apps_response.json.return_value = {
        "applications": [
            {"name": "APIM_KeyManager", "id": "apim-km"},
        ],
    }

    mock_get.side_effect = [login_response, apps_response, apps_response]

    result = orchestrator.validate_setup()
    assert result is False


@patch.object(WSO2SetupOrchestrator, "wait_for_wso2_ready")
@patch.object(WSO2SetupOrchestrator, "setup_roles_and_users")
@patch.object(WSO2SetupOrchestrator, "setup_apim_oauth_clients")
@patch.object(WSO2SetupOrchestrator, "register_darts_app")
@patch.object(WSO2SetupOrchestrator, "configure_redirect_uris")
@patch.object(WSO2SetupOrchestrator, "validate_setup")
def test_run_complete_setup_success(
    mock_validate,
    mock_redirects,
    mock_darts,
    mock_apim,
    mock_roles,
    mock_wait,
    orchestrator,
):
    """Test complete setup runs all steps successfully."""
    # All steps succeed
    mock_wait.return_value = True
    mock_roles.return_value = True
    mock_apim.return_value = True
    mock_darts.return_value = True
    mock_redirects.return_value = True
    mock_validate.return_value = True

    result = orchestrator.run_complete_setup()

    assert result is True
    mock_wait.assert_called_once()
    mock_roles.assert_called_once()
    mock_apim.assert_called_once()
    mock_darts.assert_called_once()
    mock_redirects.assert_called_once()
    mock_validate.assert_called_once()


@patch.object(WSO2SetupOrchestrator, "wait_for_wso2_ready")
@patch.object(WSO2SetupOrchestrator, "register_darts_app")
def test_run_complete_setup_wso2_not_ready(mock_darts, mock_wait, orchestrator):
    """Test complete setup aborts when WSO2 is not ready."""
    mock_wait.return_value = False

    result = orchestrator.run_complete_setup()

    assert result is False
    mock_wait.assert_called_once()
    mock_darts.assert_not_called()


@patch.object(WSO2SetupOrchestrator, "wait_for_wso2_ready")
@patch.object(WSO2SetupOrchestrator, "setup_roles_and_users")
@patch.object(WSO2SetupOrchestrator, "setup_apim_oauth_clients")
@patch.object(WSO2SetupOrchestrator, "register_darts_app")
def test_run_complete_setup_darts_app_fails(
    mock_darts,
    mock_apim,
    mock_roles,
    mock_wait,
    orchestrator,
):
    """Test complete setup fails when DartsApp registration fails."""
    mock_wait.return_value = True
    mock_roles.return_value = True
    mock_apim.return_value = True
    mock_darts.return_value = False

    result = orchestrator.run_complete_setup()

    assert result is False
    mock_darts.assert_called_once()


@patch.object(WSO2SetupOrchestrator, "wait_for_wso2_ready")
@patch.object(WSO2SetupOrchestrator, "validate_setup")
def test_run_complete_setup_skip_flags(mock_validate, mock_wait, orchestrator):
    """Test complete setup respects skip flags."""
    mock_wait.return_value = True
    mock_validate.return_value = True

    orchestrator.run_complete_setup(
        skip_roles=True,
        skip_apim=True,
        skip_darts_app=True,
        skip_redirects=True,
        validate=False,
    )

    # Should only call wait
    mock_wait.assert_called_once()
    mock_validate.assert_not_called()

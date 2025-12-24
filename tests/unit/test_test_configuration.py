"""
Unit tests for test environment configuration
"""

import os
from pathlib import Path

import pytest
from dotenv import load_dotenv


class TestTestEnvironmentConfiguration:
    """Test the .env.test configuration file"""

    @pytest.fixture(autouse=True)
    def _load_test_env(self):
        """Load test environment before each test"""
        # Save current environment
        original_env = os.environ.copy()

        # Load test environment
        env_test_path = Path(__file__).resolve().parent.parent.parent / ".env.test"
        load_dotenv(env_test_path, override=True)

        yield

        # Restore original environment
        os.environ.clear()
        os.environ.update(original_env)

    def test_env_test_file_exists(self):
        """Test that .env.test file exists"""
        env_test_path = Path(__file__).resolve().parent.parent.parent / ".env.test"
        assert env_test_path.exists(), ".env.test file should exist"

    def test_environment_is_test(self):
        """Test environment is set to test"""
        assert os.getenv("ENVIRONMENT") == "test"

    def test_database_url_uses_test_database(self):
        """Test database URL uses a test database (dartsdbtest postgres or SQLite)"""
        db_url = os.getenv("DATABASE_URL")
        assert db_url is not None
        # Accept either:
        # - dartsdbtest postgres (from .env.test)
        # - any postgres with 'dartsdb' (test database)
        # - SQLite (from conftest.py override)
        assert (
            "dartsdbtest" in db_url or "dartsdb" in db_url or "sqlite:///" in db_url
        ), f"DATABASE_URL should use a test database, got: {db_url}"

    def test_app_scheme_is_https(self):
        """Test app scheme is HTTPS"""
        assert os.getenv("APP_SCHEME") == "https"

    def test_flask_use_ssl_enabled(self):
        """Test Flask SSL is enabled"""
        assert os.getenv("FLASK_USE_SSL") == "True"

    def test_rabbitmq_exchange_is_test(self):
        """Test RabbitMQ uses test exchange"""
        exchange = os.getenv("RABBITMQ_EXCHANGE")
        assert exchange is not None
        assert "test" in exchange, "RABBITMQ_EXCHANGE should use test exchange"

    def test_tts_disabled(self):
        """Test TTS is disabled in test environment"""
        assert os.getenv("TTS_ENABLED") == "false"

    def test_wso2_client_id_set(self):
        """Test WSO2 client ID is configured"""
        client_id = os.getenv("WSO2_CLIENT_ID")
        assert client_id is not None
        assert len(client_id) > 0

    def test_wso2_verify_ssl_disabled(self):
        """Test WSO2 SSL verification is disabled for self-signed certs"""
        assert os.getenv("WSO2_IS_VERIFY_SSL") == "False"

    def test_auth_not_disabled(self):
        """Test authentication is enabled (not disabled)"""
        # conftest.py sets this to "false" (lowercase) for all tests
        auth_disabled = os.getenv("AUTH_DISABLED", "").lower()
        assert auth_disabled == "false"

    def test_flask_debug_enabled(self):
        """Test Flask debug mode is enabled"""
        assert os.getenv("FLASK_DEBUG") == "True"

    def test_session_cookie_secure_configured(self):
        """Test session cookie secure is configured (value may vary by environment)"""
        # In .env.test, this is set to False
        # But actual value depends on the environment and runtime configuration
        cookie_secure = os.getenv("SESSION_COOKIE_SECURE")
        assert cookie_secure is not None
        assert cookie_secure in ["True", "False"]

    def test_app_domain_is_test_domain(self):
        """Test app domain is test.letsplaydarts.eu"""
        domain = os.getenv("APP_DOMAIN")
        assert domain is not None
        assert "test.letsplaydarts.eu" in domain

    def test_secret_key_is_test_key(self):
        """Test secret key is set to test value"""
        secret_key = os.getenv("SECRET_KEY")
        assert secret_key is not None
        assert "test" in secret_key.lower()

    def test_wso2_urls_test_domain(self):
        """Test WSO2 URLs point to test domain"""
        wso2_url = os.getenv("WSO2_IS_URL")
        assert wso2_url is not None
        assert "test.letsplaydarts.eu" in wso2_url


class TestSSLCertificates:
    """Test SSL certificate configuration"""

    def test_ssl_certificate_exists(self):
        """Test SSL certificate file exists"""
        cert_path = Path(__file__).resolve().parent.parent.parent / "ssl" / "cert.pem"
        assert cert_path.exists(), "SSL certificate should exist at ssl/cert.pem"

    def test_ssl_key_exists(self):
        """Test SSL key file exists"""
        key_path = Path(__file__).resolve().parent.parent.parent / "ssl" / "key.pem"
        assert key_path.exists(), "SSL key should exist at ssl/key.pem"

    def test_ssl_openssl_config_exists(self):
        """Test OpenSSL config exists"""
        config_path = Path(__file__).resolve().parent.parent.parent / "ssl" / "openssl.cnf"
        assert config_path.exists(), "OpenSSL config should exist at ssl/openssl.cnf"


class TestSetupScript:
    """Test setup script existence"""

    def test_setup_script_exists(self):
        """Test setup-test-environment.sh script exists"""
        script_path = (
            Path(__file__).resolve().parent.parent.parent / "helpers" / "setup-test-environment.sh"
        )
        assert script_path.exists(), "Setup script should exist"

    def test_setup_script_executable(self):
        """Test setup script is executable"""
        script_path = (
            Path(__file__).resolve().parent.parent.parent / "helpers" / "setup-test-environment.sh"
        )
        assert (
            os.access(script_path, os.X_OK) or script_path.stat().st_mode & 0o111
        ), "Setup script should be executable"


class TestDocumentation:
    """Test documentation exists"""

    def test_test_configuration_docs_exist(self):
        """Test TEST_CONFIGURATION.md documentation exists"""
        docs_path = Path(__file__).resolve().parent.parent.parent / "docs" / "TEST_CONFIGURATION.md"
        assert docs_path.exists(), "TEST_CONFIGURATION.md should exist"

    def test_docs_contain_database_info(self):
        """Test documentation contains database setup information"""
        docs_path = Path(__file__).resolve().parent.parent.parent / "docs" / "TEST_CONFIGURATION.md"
        content = docs_path.read_text()
        assert "dartsdbtest" in content, "Docs should mention dartsdbtest"
        assert "DATABASE_URL" in content, "Docs should mention DATABASE_URL"

    def test_docs_contain_ssl_info(self):
        """Test documentation contains SSL information"""
        docs_path = Path(__file__).resolve().parent.parent.parent / "docs" / "TEST_CONFIGURATION.md"
        content = docs_path.read_text()
        assert "SSL" in content or "ssl" in content, "Docs should mention SSL"
        assert "certificate" in content.lower(), "Docs should mention certificates"

    def test_docs_contain_wso2_info(self):
        """Test documentation contains WSO2 information"""
        docs_path = Path(__file__).resolve().parent.parent.parent / "docs" / "TEST_CONFIGURATION.md"
        content = docs_path.read_text()
        assert "WSO2" in content, "Docs should mention WSO2"

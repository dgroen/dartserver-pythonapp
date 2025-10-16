"""
Unit tests for multi-environment configuration module
"""

from src.config import Config


class TestConfigMethods:
    """Test Config methods"""

    def test_get_environment_returns_string(self):
        """Test get_environment returns a string"""
        result = Config.get_environment()
        assert isinstance(result, str)
        assert result in ["production", "development", "staging"]

    def test_is_production_returns_bool(self):
        """Test is_production returns boolean"""
        result = Config.is_production()
        assert isinstance(result, bool)

    def test_is_development_returns_bool(self):
        """Test is_development returns boolean"""
        result = Config.is_development()
        assert isinstance(result, bool)

    def test_mutually_exclusive_environments(self):
        """Test that is_production and is_development are mutually exclusive"""
        if Config.is_production():
            assert not Config.is_development()
        elif Config.is_development():
            assert not Config.is_production()


class TestConfigUrls:
    """Test URL properties"""

    def test_app_domain_is_string(self):
        """Test APP_DOMAIN is a string"""
        assert isinstance(Config.APP_DOMAIN, str)
        assert len(Config.APP_DOMAIN) > 0

    def test_app_scheme_is_valid(self):
        """Test APP_SCHEME is valid"""
        assert Config.APP_SCHEME in ["http", "https"]

    def test_app_url_format(self):
        """Test APP_URL has correct format"""
        assert Config.APP_URL.startswith(Config.APP_SCHEME + "://")
        assert Config.APP_DOMAIN in Config.APP_URL

    def test_callback_url_format(self):
        """Test CALLBACK_URL has correct format"""
        assert Config.CALLBACK_URL.startswith(Config.APP_SCHEME + "://")
        assert Config.CALLBACK_URL.endswith("/callback")

    def test_logout_redirect_url_format(self):
        """Test LOGOUT_REDIRECT_URL has correct format"""
        assert Config.LOGOUT_REDIRECT_URL.startswith(Config.APP_SCHEME + "://")
        assert Config.LOGOUT_REDIRECT_URL.endswith("/")

    def test_callback_url_consistency(self):
        """Test CALLBACK_URL is consistent with APP_URL"""
        expected_callback = Config.APP_URL + "/callback"
        assert expected_callback == Config.CALLBACK_URL

    def test_logout_redirect_url_consistency(self):
        """Test LOGOUT_REDIRECT_URL is consistent with APP_URL"""
        expected_logout = Config.APP_URL + "/"
        assert expected_logout == Config.LOGOUT_REDIRECT_URL

    def test_get_app_url_without_path(self):
        """Test get_app_url without path"""
        result = Config.get_app_url()
        assert result == Config.APP_URL

    def test_get_app_url_with_path_no_leading_slash(self):
        """Test get_app_url with path (no leading slash)"""
        result = Config.get_app_url("api/games")
        assert result == Config.APP_URL + "/api/games"

    def test_get_app_url_with_path_with_leading_slash(self):
        """Test get_app_url with path (with leading slash)"""
        result = Config.get_app_url("/api/games")
        assert result == Config.APP_URL + "/api/games"

    def test_get_app_url_returns_string(self):
        """Test get_app_url returns string"""
        result = Config.get_app_url()
        assert isinstance(result, str)


class TestConfigSecurity:
    """Test security-related configuration"""

    def test_session_cookie_secure_is_bool(self):
        """Test SESSION_COOKIE_SECURE is boolean"""
        assert isinstance(Config.SESSION_COOKIE_SECURE, bool)

    def test_flask_use_ssl_is_bool(self):
        """Test FLASK_USE_SSL is boolean"""
        assert isinstance(Config.FLASK_USE_SSL, bool)

    def test_session_cookie_secure_matches_scheme_when_https(self):
        """Test SESSION_COOKIE_SECURE should be true for https"""
        if Config.APP_SCHEME == "https":
            assert Config.SESSION_COOKIE_SECURE is True

    def test_session_cookie_secure_can_be_false_for_http(self):
        """Test SESSION_COOKIE_SECURE should be false for http (or can be)"""
        if Config.APP_SCHEME == "http":
            # Can be True or False but typically False
            assert isinstance(Config.SESSION_COOKIE_SECURE, bool)

    def test_swagger_host_is_string(self):
        """Test SWAGGER_HOST is a string"""
        assert isinstance(Config.SWAGGER_HOST, str)
        assert len(Config.SWAGGER_HOST) > 0


class TestConfigRepresentation:
    """Test configuration representation"""

    def test_config_repr_is_string(self):
        """Test Config repr returns a string"""
        repr_str = repr(Config)
        assert isinstance(repr_str, str)
        # Should contain 'Config'
        assert "Config" in repr_str


class TestConfigProductionSetup:
    """Test production configuration consistency"""

    def test_production_uses_https(self):
        """Test production environment uses https"""
        if Config.is_production():
            assert Config.APP_SCHEME == "https"
            assert Config.SESSION_COOKIE_SECURE is True

    def test_production_domain_no_localhost(self):
        """Test production domain is not localhost"""
        if Config.is_production():
            assert "localhost" not in Config.APP_DOMAIN
            assert "127.0.0.1" not in Config.APP_DOMAIN


class TestConfigDevelopmentSetup:
    """Test development configuration consistency"""

    def test_development_can_use_http(self):
        """Test development can use http"""
        if Config.is_development():
            # Development typically uses http, but this is flexible
            assert Config.APP_SCHEME in ["http", "https"]


class TestConfigEnvironmentVariable:
    """Test environment variable reading"""

    def test_environment_is_string(self):
        """Test ENVIRONMENT is a string"""
        assert isinstance(Config.ENVIRONMENT, str)

    def test_environment_is_valid_value(self):
        """Test ENVIRONMENT is a valid value"""
        assert Config.ENVIRONMENT in ["production", "development", "staging"]

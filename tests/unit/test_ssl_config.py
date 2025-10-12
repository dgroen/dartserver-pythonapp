"""
Unit tests for SSL configuration
"""

import os
from pathlib import Path
from unittest.mock import patch

import pytest


class TestSSLConfiguration:
    """Test SSL configuration and error handling"""

    def test_ssl_certificates_exist(self):
        """Test that SSL certificates exist"""
        ssl_dir = Path(__file__).parent.parent.parent / "ssl"
        cert_file = ssl_dir / "cert.pem"
        key_file = ssl_dir / "key.pem"

        assert cert_file.exists(), "SSL certificate not found"
        assert key_file.exists(), "SSL private key not found"

    def test_ssl_certificate_validity(self):
        """Test that SSL certificate is valid"""
        import subprocess

        ssl_dir = Path(__file__).parent.parent.parent / "ssl"
        cert_file = ssl_dir / "cert.pem"

        # Check certificate can be read
        result = subprocess.run(
            ["openssl", "x509", "-in", str(cert_file), "-noout", "-subject"],
            check=False,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, "Certificate is not valid"
        assert "letsplaydarts.eu" in result.stdout, "Certificate domain mismatch"

    def test_ssl_certificate_san(self):
        """Test that SSL certificate has correct Subject Alternative Names"""
        import subprocess

        ssl_dir = Path(__file__).parent.parent.parent / "ssl"
        cert_file = ssl_dir / "cert.pem"

        # Check SAN
        result = subprocess.run(
            [
                "openssl",
                "x509",
                "-in",
                str(cert_file),
                "-noout",
                "-ext",
                "subjectAltName",
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, "Failed to read certificate SAN"
        assert "letsplaydarts.eu" in result.stdout
        assert "localhost" in result.stdout
        assert "127.0.0.1" in result.stdout

    def test_ssl_key_permissions(self):
        """Test that SSL private key has correct permissions"""
        ssl_dir = Path(__file__).parent.parent.parent / "ssl"
        key_file = ssl_dir / "key.pem"

        # Check file permissions (should be 600 or more restrictive)
        stat_info = os.stat(key_file)
        mode = stat_info.st_mode & 0o777

        # Key should not be world-readable
        assert mode & 0o004 == 0, "Private key is world-readable"

    @patch.dict(os.environ, {"FLASK_USE_SSL": "True"})
    def test_ssl_enabled_env_var(self):
        """Test SSL enabled via environment variable"""
        use_ssl = os.getenv("FLASK_USE_SSL", "False").lower() == "true"
        assert use_ssl is True

    @patch.dict(os.environ, {"FLASK_USE_SSL": "False"})
    def test_ssl_disabled_env_var(self):
        """Test SSL disabled via environment variable"""
        use_ssl = os.getenv("FLASK_USE_SSL", "False").lower() == "true"
        assert use_ssl is False

    def test_ssl_default_disabled(self):
        """Test SSL is disabled by default"""
        with patch.dict(os.environ, {}, clear=True):
            use_ssl = os.getenv("FLASK_USE_SSL", "False").lower() == "true"
            assert use_ssl is False

    def test_hosts_file_entry(self):
        """Test that domain is in /etc/hosts"""
        try:
            with open("/etc/hosts") as f:
                hosts_content = f.read()
            assert "letsplaydarts.eu" in hosts_content, "Domain not found in /etc/hosts"
        except PermissionError:
            pytest.skip("Cannot read /etc/hosts (permission denied)")

    def test_ssl_certificate_key_match(self):
        """Test that certificate and key match"""
        import subprocess

        ssl_dir = Path(__file__).parent.parent.parent / "ssl"
        cert_file = ssl_dir / "cert.pem"
        key_file = ssl_dir / "key.pem"

        # Get certificate modulus
        cert_result = subprocess.run(
            ["openssl", "x509", "-noout", "-modulus", "-in", str(cert_file)],
            check=False,
            capture_output=True,
            text=True,
        )

        # Get key modulus
        key_result = subprocess.run(
            ["openssl", "rsa", "-noout", "-modulus", "-in", str(key_file)],
            check=False,
            capture_output=True,
            text=True,
        )

        assert cert_result.returncode == 0, "Failed to read certificate modulus"
        assert key_result.returncode == 0, "Failed to read key modulus"
        assert cert_result.stdout == key_result.stdout, "Certificate and key do not match"

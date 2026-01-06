#!/usr/bin/env python3
"""
Complete WSO2 Identity Server Setup Script
Orchestrates all setup steps: DB init, roles/users, OAuth clients, redirects
Can be used in CI/CD pipelines for test and production deployments
"""

import argparse
import logging
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv

# Disable SSL warnings for self-signed certificates
requests.packages.urllib3.disable_warnings()  # type: ignore

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)


class WSO2SetupOrchestrator:
    """Orchestrates complete WSO2 IS setup for deployment environments."""

    def __init__(self, env_file: str | None = None, environment: str = "development"):
        """Initialize orchestrator with environment configuration.

        Args:
            env_file: Path to .env file (default: auto-detect)
            environment: Environment name (development, test, production)
        """
        self.environment = environment
        self.helpers_dir = Path(__file__).parent
        self.repo_root = self.helpers_dir.parent
        self.env_file = self._resolve_env_file(env_file)

        # Load environment variables
        if self.env_file.exists():
            load_dotenv(self.env_file)
            logger.info(f"Loaded environment from: {self.env_file}")
        else:
            logger.warning(f"Environment file not found: {self.env_file}")

        # WSO2 configuration
        self.wso2_url = os.getenv("WSO2_IS_URL", "https://localhost:9443")
        self.wso2_admin_user = os.getenv("WSO2_ADMIN_USERNAME", "admin")
        self.wso2_admin_password = os.getenv("WSO2_ADMIN_PASSWORD", "admin")
        self.wso2_verify_ssl = os.getenv("WSO2_IS_VERIFY_SSL", "False").lower() == "true"

        # Application configuration
        self.client_id = os.getenv("WSO2_CLIENT_ID", "")
        self.redirect_uri = os.getenv("WSO2_REDIRECT_URI", "https://localhost:5000/callback")
        self.post_logout_uri = os.getenv(
            "WSO2_POST_LOGOUT_REDIRECT_URI",
            "https://localhost:5000/",
        )

        logger.info(f"Environment: {self.environment}")
        logger.info(f"WSO2 IS URL: {self.wso2_url}")

    def _resolve_env_file(self, env_file: str | None) -> Path:
        """Resolve environment file path based on environment."""
        if env_file:
            return Path(env_file)

        # Auto-detect based on environment
        env_files = {
            "test": self.helpers_dir.parent / ".env.test",
            "production": self.helpers_dir.parent / ".env.production",
            "staging": self.helpers_dir.parent / ".env.staging",
            "development": self.helpers_dir.parent / ".env",
        }

        env_path = env_files.get(self.environment, self.helpers_dir.parent / ".env")
        if not env_path.exists():
            # Fallback to default .env
            env_path = self.helpers_dir.parent / ".env"

        return env_path

    def wait_for_wso2_ready(self, max_retries: int = 60, retry_delay: int = 5) -> bool:
        """Wait for WSO2 IS to be ready.

        Args:
            max_retries: Maximum number of retry attempts
            retry_delay: Delay in seconds between retries

        Returns:
            True if WSO2 is ready, False otherwise
        """
        logger.info("⏳ Waiting for WSO2 IS to be ready...")

        for attempt in range(1, max_retries + 1):
            try:
                response = requests.get(
                    f"{self.wso2_url}/carbon/admin/login.jsp",
                    verify=self.wso2_verify_ssl,
                    timeout=5,
                )
                if response.status_code == 200:
                    logger.info("✅ WSO2 IS is ready!")
                    return True
            except requests.exceptions.RequestException:
                if attempt >= max_retries:
                    break

            if attempt < max_retries:
                logger.info(f"   Retry {attempt}/{max_retries}... (waiting {retry_delay}s)")
                time.sleep(retry_delay)

        logger.error("❌ WSO2 IS did not become ready in time")
        return False

    def run_script(self, script_name: str, description: str, **kwargs: Any) -> bool:
        """Run a helper script.

        Args:
            script_name: Name of the script to run (without path)
            description: Human-readable description of what the script does
            **kwargs: Additional environment variables to pass

        Returns:
            True if script succeeded, False otherwise
        """
        script_path = self.helpers_dir / script_name

        if not script_path.exists():
            logger.error(f"❌ Script not found: {script_path}")
            return False

        logger.info(f"\n{'=' * 70}")
        logger.info(f"Running: {description}")
        logger.info(f"Script: {script_name}")
        logger.info(f"{'=' * 70}")

        # Build environment
        env = os.environ.copy()
        env.update(kwargs)

        try:
            result = subprocess.run(  # noqa: S603
                [sys.executable, str(script_path)],
                env=env,
                cwd=str(self.repo_root),
                capture_output=False,
                check=False,
            )

            if result.returncode == 0:
                logger.info(f"✅ {description} - SUCCESS")
                return True

            logger.error(f"❌ {description} - FAILED (exit code: {result.returncode})")
            return False

        except Exception as exc:
            logger.exception(f"❌ Error running {script_name}: {exc}")
            return False

    def setup_roles_and_users(self) -> bool:
        """Setup WSO2 roles and users via SCIM2."""
        return self.run_script(
            "setup_wso2_roles.py",
            "Setup WSO2 roles and users",
        )

    def setup_apim_oauth_clients(self) -> bool:
        """Setup OAuth2 clients for APIM via DCR."""
        return self.run_script(
            "configure_wso2_oauth_apps.py",
            "Configure APIM OAuth2 clients",
        )

    def register_darts_app(self) -> bool:
        """Register DartsApp OAuth2 client."""
        return self.run_script(
            "register_darts_app.py",
            "Register DartsApp OAuth2 client",
        )

    def configure_redirect_uris(self) -> bool:
        """Configure OAuth2 redirect URIs."""
        return self.run_script(
            "configure_wso2_redirects.py",
            "Configure OAuth2 redirect URIs",
        )

    def validate_setup(self) -> bool:
        """Validate that the setup completed successfully.

        Returns:
            True if validation passed, False otherwise
        """
        logger.info("\n%s", "=" * 70)
        logger.info("Validating WSO2 setup...")
        logger.info("%s", "=" * 70)

        checks = []

        # Check 1: WSO2 IS is accessible
        try:
            response = requests.get(
                f"{self.wso2_url}/carbon/admin/login.jsp",
                verify=self.wso2_verify_ssl,
                timeout=5,
            )
            if response.status_code == 200:
                logger.info("✅ WSO2 IS is accessible")
                checks.append(True)
            else:
                logger.error(f"❌ WSO2 IS returned status: {response.status_code}")
                checks.append(False)
        except Exception as exc:
            logger.error(f"❌ WSO2 IS not accessible: {exc}")
            checks.append(False)

        # Check 2: DartsApp exists
        try:
            response = requests.get(
                f"{self.wso2_url}/api/server/v1/applications",
                auth=(self.wso2_admin_user, self.wso2_admin_password),
                headers={"Accept": "application/json"},
                verify=self.wso2_verify_ssl,
                timeout=10,
            )
            if response.status_code == 200:
                apps = response.json().get("applications", [])
                darts_app = next((app for app in apps if app.get("name") == "DartsApp"), None)
                if darts_app:
                    logger.info(f"✅ DartsApp exists (ID: {darts_app.get('id')})")
                    checks.append(True)
                else:
                    logger.error("❌ DartsApp not found")
                    checks.append(False)
            else:
                logger.error(f"❌ Failed to list applications: {response.status_code}")
                checks.append(False)
        except Exception as exc:
            logger.error(f"❌ Error checking DartsApp: {exc}")
            checks.append(False)

        # Check 3: APIM OAuth clients exist
        apim_clients = ["APIM_KeyManager", "APIM_Publisher", "APIM_DevPortal", "APIM_Admin"]
        try:
            response = requests.get(
                f"{self.wso2_url}/api/server/v1/applications",
                auth=(self.wso2_admin_user, self.wso2_admin_password),
                headers={"Accept": "application/json"},
                verify=self.wso2_verify_ssl,
                timeout=10,
            )
            if response.status_code == 200:
                apps = response.json().get("applications", [])
                app_names = {app.get("name") for app in apps}
                found_clients = [client for client in apim_clients if client in app_names]
                if len(found_clients) == len(apim_clients):
                    logger.info(f"✅ All APIM OAuth clients exist: {', '.join(found_clients)}")
                    checks.append(True)
                else:
                    missing = set(apim_clients) - set(found_clients)
                    logger.warning(f"⚠️  Missing APIM clients: {', '.join(missing)}")
                    checks.append(False)
            else:
                logger.error(f"❌ Failed to list applications: {response.status_code}")
                checks.append(False)
        except Exception as exc:
            logger.error(f"❌ Error checking APIM clients: {exc}")
            checks.append(False)

        # Overall validation
        all_passed = all(checks)
        logger.info("\n%s", "=" * 70)
        if all_passed:
            logger.info("✅ All validation checks passed!")
        else:
            logger.error(f"❌ {sum(not c for c in checks)}/{len(checks)} validation checks failed")
        logger.info("%s", "=" * 70)

        return all_passed

    def run_complete_setup(
        self,
        skip_wait: bool = False,
        skip_roles: bool = False,
        skip_apim: bool = False,
        skip_darts_app: bool = False,
        skip_redirects: bool = False,
        validate: bool = True,
    ) -> bool:
        """Run complete WSO2 setup.

        Args:
            skip_wait: Skip waiting for WSO2 to be ready
            skip_roles: Skip roles/users setup
            skip_apim: Skip APIM OAuth clients setup
            skip_darts_app: Skip DartsApp registration
            skip_redirects: Skip redirect URIs configuration
            validate: Run validation after setup

        Returns:
            True if setup succeeded, False otherwise
        """
        logger.info("\n%s", "=" * 70)
        logger.info("WSO2 Identity Server - Complete Setup")
        logger.info("%s", "=" * 70)
        logger.info(f"Environment: {self.environment}")
        logger.info(f"WSO2 IS URL: {self.wso2_url}")
        logger.info(f"Redirect URI: {self.redirect_uri}")
        logger.info("%s\n", "=" * 70)

        steps = []

        # Step 1: Wait for WSO2
        if not skip_wait:
            if not self.wait_for_wso2_ready():
                logger.error("❌ WSO2 IS is not ready - aborting setup")
                return False
            steps.append(("Wait for WSO2", True))
        else:
            logger.info("⏭️  Skipping wait for WSO2 (--skip-wait)")

        # Step 2: Setup roles and users
        if not skip_roles:
            result = self.setup_roles_and_users()
            steps.append(("Setup roles/users", result))
            if not result:
                logger.warning("⚠️  Roles/users setup failed - continuing...")
        else:
            logger.info("⏭️  Skipping roles/users setup (--skip-roles)")

        # Step 3: Setup APIM OAuth clients
        if not skip_apim:
            result = self.setup_apim_oauth_clients()
            steps.append(("APIM OAuth clients", result))
            if not result:
                logger.warning("⚠️  APIM OAuth setup failed - continuing...")
        else:
            logger.info("⏭️  Skipping APIM OAuth clients (--skip-apim)")

        # Step 4: Register DartsApp
        if not skip_darts_app:
            result = self.register_darts_app()
            steps.append(("Register DartsApp", result))
            if not result:
                logger.error("❌ DartsApp registration failed - this is critical!")
                return False
        else:
            logger.info("⏭️  Skipping DartsApp registration (--skip-darts-app)")

        # Step 5: Configure redirect URIs
        if not skip_redirects:
            result = self.configure_redirect_uris()
            steps.append(("Configure redirects", result))
            if not result:
                logger.warning("⚠️  Redirect configuration failed - continuing...")
        else:
            logger.info("⏭️  Skipping redirect configuration (--skip-redirects)")

        # Step 6: Validate setup
        if validate:
            result = self.validate_setup()
            steps.append(("Validation", result))
        else:
            logger.info("⏭️  Skipping validation (--no-validate)")

        # Print summary
        logger.info("\n%s", "=" * 70)
        logger.info("Setup Summary")
        logger.info("%s", "=" * 70)
        for step_name, step_result in steps:
            status = "✅ SUCCESS" if step_result else "❌ FAILED"
            logger.info(f"{step_name:.<50} {status}")
        logger.info("=" * 70)

        all_succeeded = all(result for _, result in steps)

        if all_succeeded:
            logger.info("\n✅ WSO2 setup completed successfully!")
            logger.info("\nNext steps:")
            logger.info("1. Restart APIM to pick up new OAuth client credentials")
            logger.info("   docker-compose restart wso2apim")
            logger.info("2. Update application .env with DartsApp client credentials")
            logger.info("3. Restart application to use new credentials")
            logger.info("   docker-compose restart darts-app")
            return True

        logger.error("\n❌ WSO2 setup completed with errors")
        logger.info("\nTroubleshooting:")
        logger.info("1. Check WSO2 IS logs: docker-compose logs wso2is")
        logger.info("2. Verify WSO2 IS is accessible: curl -k %s", self.wso2_url)
        logger.info("3. Re-run with individual steps using --skip-* flags")
        return False


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Complete WSO2 Identity Server setup for deployment environments",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full setup for development
  python3 setup_wso2_complete.py --env development

  # Full setup for test environment
  python3 setup_wso2_complete.py --env test --env-file .env.test

  # Production setup with custom env file
  python3 setup_wso2_complete.py --env production --env-file /path/to/.env.production

  # Skip certain steps
  python3 setup_wso2_complete.py --skip-apim --skip-roles

  # Run without validation
  python3 setup_wso2_complete.py --no-validate
        """,
    )

    parser.add_argument(
        "--env",
        default="development",
        choices=["development", "test", "staging", "production"],
        help="Target environment (default: development)",
    )
    parser.add_argument(
        "--env-file",
        help="Path to .env file (default: auto-detect based on environment)",
    )
    parser.add_argument(
        "--skip-wait",
        action="store_true",
        help="Skip waiting for WSO2 to be ready",
    )
    parser.add_argument(
        "--skip-roles",
        action="store_true",
        help="Skip roles/users setup",
    )
    parser.add_argument(
        "--skip-apim",
        action="store_true",
        help="Skip APIM OAuth clients setup",
    )
    parser.add_argument(
        "--skip-darts-app",
        action="store_true",
        help="Skip DartsApp registration",
    )
    parser.add_argument(
        "--skip-redirects",
        action="store_true",
        help="Skip redirect URIs configuration",
    )
    parser.add_argument(
        "--no-validate",
        action="store_true",
        help="Skip validation after setup",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    orchestrator = WSO2SetupOrchestrator(
        env_file=args.env_file,
        environment=args.env,
    )

    success = orchestrator.run_complete_setup(
        skip_wait=args.skip_wait,
        skip_roles=args.skip_roles,
        skip_apim=args.skip_apim,
        skip_darts_app=args.skip_darts_app,
        skip_redirects=args.skip_redirects,
        validate=not args.no_validate,
    )

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())

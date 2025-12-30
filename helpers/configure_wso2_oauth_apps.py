#!/usr/bin/env python3
"""
Configure WSO2 IS OAuth2 clients for APIM via Dynamic Client Registration (DCR).
"""

import argparse
import re
import sys
import time
from pathlib import Path

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class WSO2DCRConfigurator:
    """Configure OAuth2 clients via Dynamic Client Registration."""

    def __init__(
        self,
        is_host: str,
        is_port: int,
        username: str,
        password: str,
        apim_host: str,
        apim_port: int,
    ):
        self.is_base_url = f"https://{is_host}:{is_port}"
        self.dcr_url = f"{self.is_base_url}/api/identity/oauth2/dcr/v1.1/register"
        self.is_app_url = f"{self.is_base_url}/api/server/v1/applications"
        self.username = username
        self.password = password
        self.apim_host = apim_host
        self.apim_port = apim_port

    def register_client_via_dcr(self, client_config: dict) -> dict | None:
        """Register an OAuth2 client via Dynamic Client Registration."""
        client_name = client_config["name"]
        print(f"\nRegistering OAuth2 client: {client_name}")

        headers = {"Content-Type": "application/json"}
        payload = {
            "client_name": client_name,
            "redirect_uris": client_config["redirect_uris"],
            "grant_types": client_config["grant_types"],
            "token_endpoint_auth_method": "client_secret_basic",
        }

        try:
            response = requests.post(
                self.dcr_url,
                headers=headers,
                json=payload,
                auth=(self.username, self.password),
                verify=False,
                timeout=10,
            )
            print(f"  Response status: {response.status_code}")

            if response.status_code == 201:
                data = response.json()
                client_id = data.get("client_id")
                client_secret = data.get("client_secret")
                if not client_id or not client_secret:
                    print("✗ Missing client_id or client_secret in response")
                    return None
                print(f"  ✓ Client ID: {client_id[:20]}...")
                print(f"  ✓ Client Secret: {client_secret[:20]}...")
                return {
                    "name": client_name,
                    "client_id": client_id,
                    "client_secret": client_secret,
                }
            print(f"✗ Failed to register client: {response.status_code}")
            if response.text:
                print(f"  Response: {response.text[:200]}")
            return None
        except Exception as e:
            print(f"✗ Error registering client: {e}")
            return None

    def delete_client_via_dcr(self, app_id: str, client_name: str) -> bool:
        """Delete an OAuth2 client via Application Management API."""
        print(f"  Deleting: {client_name}")
        url = f"{self.is_app_url}/{app_id}"
        try:
            response = requests.delete(
                url,
                auth=(self.username, self.password),
                verify=False,
                timeout=10,
            )
            if response.status_code in [200, 204]:
                print(f"  ✓ Deleted: {client_name}")
                return True
            if response.status_code == 404:
                print(f"  ✓ Already deleted: {client_name}")
                return True
            print(f"  ✗ Failed: {response.status_code}")
            if response.text:
                print(f"     Response: {response.text[:100]}")
            return False
        except Exception as e:
            print(f"  ✗ Error: {e}")
            return False

    def list_clients_via_dcr(self) -> list:
        """List all applications in WSO2 IS."""
        try:
            response = requests.get(
                self.is_app_url,
                auth=(self.username, self.password),
                verify=False,
                timeout=10,
            )
            if response.status_code == 200:
                return response.json().get("applications", [])
            return []
        except Exception as e:
            print(f"Error listing applications: {e}")
            return []

    def cleanup_existing_clients(self):
        """Delete existing APIM OAuth2 clients."""
        print("\nCleaning up existing APIM OAuth2 clients...")
        clients_to_remove = ["APIM_KeyManager", "APIM_Publisher", "APIM_DevPortal", "APIM_Admin"]
        existing_apps = self.list_clients_via_dcr()
        for app in existing_apps:
            if app.get("name") in clients_to_remove:
                self.delete_client_via_dcr(app.get("id"), app.get("name"))
                time.sleep(0.3)
        print("✓ Cleanup complete")

    def configure_all(self, cleanup: bool = False) -> dict[str, dict]:
        """Configure all APIM OAuth2 clients via DCR."""
        if cleanup:
            self.cleanup_existing_clients()
        results = {}
        clients = [
            {
                "name": "APIM_KeyManager",
                "redirect_uris": [f"https://{self.apim_host}:{self.apim_port}/commonauth"],
                "grant_types": ["client_credentials", "password", "refresh_token"],
            },
            {
                "name": "APIM_Publisher",
                "redirect_uris": [
                    f"https://{self.apim_host}:{self.apim_port}/publisher/services/auth/callback/login",
                ],
                "grant_types": ["authorization_code", "refresh_token"],
            },
            {
                "name": "APIM_DevPortal",
                "redirect_uris": [
                    f"https://{self.apim_host}:{self.apim_port}/devportal/services/auth/callback/login",
                ],
                "grant_types": ["authorization_code", "refresh_token"],
            },
            {
                "name": "APIM_Admin",
                "redirect_uris": [
                    f"https://{self.apim_host}:{self.apim_port}/admin/services/auth/callback/login",
                ],
                "grant_types": ["authorization_code", "refresh_token"],
            },
        ]
        for client_config in clients:
            credentials = self.register_client_via_dcr(client_config)
            if credentials:
                results[client_config["name"]] = credentials
            time.sleep(0.5)
        return results

    def update_deployment_toml(self, results: dict[str, dict], toml_path: str) -> bool:
        """Update deployment.toml with OAuth2 client credentials."""
        print("\n" + "=" * 70)
        print("UPDATING DEPLOYMENT.TOML")
        print("=" * 70)
        try:
            with Path(toml_path).open() as f:
                content = f.read()

            if "APIM_KeyManager" in results:
                km = results["APIM_KeyManager"]
                lines = content.split("\n")
                in_keymanager = False
                last_username_idx = -1
                last_password_idx = -1
                for i, line in enumerate(lines):
                    if "[keymanager.default]" in line:
                        in_keymanager = True
                    elif line.startswith("[") and "[keymanager.default" not in line:
                        in_keymanager = False
                    elif in_keymanager:
                        if line.strip().startswith("username = "):
                            last_username_idx = i
                        elif line.strip().startswith("password = "):
                            last_password_idx = i
                if last_username_idx >= 0 and last_password_idx >= 0:
                    lines[last_username_idx] = f'username = "{km["client_id"]}"'
                    lines[last_password_idx] = f'password = "{km["client_secret"]}"'
                    content = "\n".join(lines)
                    print("  ✓ Updated Key Manager credentials")

            if "APIM_Publisher" in results:
                pub = results["APIM_Publisher"]
                client_id = pub["client_id"]
                client_secret = pub["client_secret"]
                oidc_section = f"""[oauth2.oidc]
client_id = "{client_id}"
client_secret = "{client_secret}"
server_url = "https://wso2is:9443"
authorize_endpoint = "https://wso2is:9443/oauth2/authorize"
token_endpoint = "https://wso2is:9443/oauth2/token"
revoke_endpoint = "https://wso2is:9443/oauth2/revoke"
userinfo_endpoint = "https://wso2is:9443/oauth2/userinfo"
oidc_logout_endpoint = "https://wso2is:9443/oidc/logout"
oidc_session_iframe_endpoint = "https://wso2is:9443/oidc/checksession"
scope = "openid profile email"
"""
                if "[oauth2.oidc]" in content:
                    pattern = r"\[oauth2\.oidc\].*?(?=\n\[|$)"
                    content = re.sub(pattern, oidc_section.rstrip(), content, flags=re.DOTALL)
                    print("  ✓ Updated [oauth2.oidc] section")
                else:
                    content = content.rstrip() + "\n\n" + oidc_section
                    print("  ✓ Added [oauth2.oidc] section")

            with Path(toml_path).open("w") as f:
                f.write(content)
            print(f"  ✓ Successfully updated {toml_path}")
            return True
        except Exception as e:
            print(f"  ✗ Error: {e}")
            return False

    def print_configuration_summary(self, results: dict[str, dict]):
        """Print configuration summary."""
        print("\n" + "=" * 70)
        print("OAUTH2 CLIENTS REGISTERED SUCCESSFULLY")
        print("=" * 70)
        for client_name, creds in results.items():
            print(f"\n{client_name}")
            print(f"  Client ID:     {creds['client_id']}")
            print(f"  Client Secret: {creds['client_secret']}")
        print("\n" + "=" * 70)
        print("CONFIGURATION SAVED")
        print("=" * 70)
        print("\nUpdated sections in deployment.toml:")
        print("  - [keymanager.default] → username/password (APIM_KeyManager)")
        print("  - [oauth2.oidc] → client_id/client_secret (APIM_Publisher)\n")


def main():
    parser = argparse.ArgumentParser(
        description="Configure WSO2 IS OAuth2 clients for APIM via DCR",
    )
    parser.add_argument(
        "--is-host",
        default="localhost",
        help="WSO2 IS hostname (default: localhost)",
    )
    parser.add_argument("--is-port", type=int, default=9443, help="WSO2 IS port (default: 9443)")
    parser.add_argument(
        "--username",
        default="admin",
        help="WSO2 IS admin username (default: admin)",
    )
    parser.add_argument(
        "--password",
        default="admin",
        help="WSO2 IS admin password (default: admin)",
    )
    parser.add_argument(
        "--apim-host",
        default="localhost",
        help="WSO2 APIM hostname (default: localhost)",
    )
    parser.add_argument(
        "--apim-port",
        type=int,
        default=9444,
        help="WSO2 APIM port (default: 9444)",
    )
    parser.add_argument(
        "--update-toml",
        default="wso2apim-4-config/deployment.toml",
        help="Path to deployment.toml (default: wso2apim-4-config/deployment.toml)",
    )
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Delete existing APIM OAuth2 clients before registering new ones",
    )

    args = parser.parse_args()
    configurator = WSO2DCRConfigurator(
        args.is_host,
        args.is_port,
        args.username,
        args.password,
        args.apim_host,
        args.apim_port,
    )

    print("=" * 70)
    print("WSO2 IS OAuth2 Configuration for APIM (via DCR)")
    print("=" * 70)
    print(f"WSO2 IS: https://{args.is_host}:{args.is_port}")
    print(f"WSO2 APIM: https://{args.apim_host}:{args.apim_port}")
    print("=" * 70)

    results = configurator.configure_all(cleanup=args.cleanup)

    if results:
        configurator.print_configuration_summary(results)
        if args.update_toml:
            configurator.update_deployment_toml(results, args.update_toml)
        print("=" * 70)
        print("Next steps:")
        print("1. Verify deployment.toml was updated correctly")
        print("2. Restart APIM: docker-compose restart wso2apim")
        print("3. Test Publisher: https://localhost:9444/publisher")
        print("=" * 70 + "\n")
        return 0
    print("\n✗ OAuth2 client registration failed")
    return 1


if __name__ == "__main__":
    sys.exit(main())

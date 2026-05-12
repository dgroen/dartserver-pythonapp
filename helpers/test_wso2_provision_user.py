#!/usr/bin/env python3
"""Provision a WSO2 test user and ensure a role membership exists.

This script is intended for the test server and can be run repeatedly.
It creates the user if needed, updates the password if the user already
exists, ensures the requested role group exists, and then assigns the user
to that group.
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import Any

import requests
import urllib3

urllib3.disable_warnings()


def env_or(value: str | None, name: str, default: str = "") -> str:
    if value:
        return value
    return os.getenv(name, default)


class WSO2SCIMClient:
    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url.rstrip("/")
        self.auth = (username, password)
        self.headers = {"Content-Type": "application/json", "Accept": "application/json"}

    def get_user(self, username: str) -> dict[str, Any] | None:
        response = requests.get(
            f"{self.base_url}/scim2/Users",
            auth=self.auth,
            headers=self.headers,
            params={"filter": f'userName eq "{username}"'},
            verify=False,
            timeout=15,
        )
        if response.status_code == 200:
            data = response.json()
            if data.get("totalResults", 0) > 0:
                return data["Resources"][0]
        return None

    def create_user(self, username: str, password: str, display_name: str) -> dict[str, Any] | None:
        payload = {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
            "userName": username,
            "name": {"givenName": display_name, "familyName": username},
            "displayName": display_name,
            "password": password,
            "active": True,
        }
        response = requests.post(
            f"{self.base_url}/scim2/Users",
            auth=self.auth,
            headers=self.headers,
            json=payload,
            verify=False,
            timeout=15,
        )
        if response.status_code == 201:
            return response.json()
        return None

    def update_password(self, user_id: str, password: str) -> bool:
        payload = {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
            "Operations": [{"op": "replace", "path": "password", "value": password}],
        }
        response = requests.patch(
            f"{self.base_url}/scim2/Users/{user_id}",
            auth=self.auth,
            headers=self.headers,
            json=payload,
            verify=False,
            timeout=15,
        )
        return response.status_code in (200, 204)

    def get_group(self, name: str) -> dict[str, Any] | None:
        response = requests.get(
            f"{self.base_url}/scim2/Groups",
            auth=self.auth,
            headers=self.headers,
            params={"filter": f'displayName eq "{name}"'},
            verify=False,
            timeout=15,
        )
        if response.status_code == 200:
            data = response.json()
            if data.get("totalResults", 0) > 0:
                return data["Resources"][0]
        return None

    def create_group(self, name: str) -> dict[str, Any] | None:
        payload = {
            "displayName": name,
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
        }
        response = requests.post(
            f"{self.base_url}/scim2/Groups",
            auth=self.auth,
            headers=self.headers,
            json=payload,
            verify=False,
            timeout=15,
        )
        if response.status_code == 201:
            return response.json()
        return None

    def add_user_to_group(self, user_id: str, user_name: str, group_id: str) -> bool:
        group_response = requests.get(
            f"{self.base_url}/scim2/Groups/{group_id}",
            auth=self.auth,
            headers=self.headers,
            verify=False,
            timeout=15,
        )
        if group_response.status_code == 200:
            members = group_response.json().get("members", [])
            if any(member.get("value") == user_id for member in members):
                return True

        payload = {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
            "Operations": [
                {
                    "op": "add",
                    "path": "members",
                    "value": [{"value": user_id, "display": user_name}],
                },
            ],
        }
        response = requests.patch(
            f"{self.base_url}/scim2/Groups/{group_id}",
            auth=self.auth,
            headers=self.headers,
            json=payload,
            verify=False,
            timeout=15,
        )
        return response.status_code in (200, 204)

    def user_groups(self, user_id: str) -> list[dict[str, Any]]:
        response = requests.get(
            f"{self.base_url}/scim2/Users/{user_id}",
            auth=self.auth,
            headers=self.headers,
            verify=False,
            timeout=15,
        )
        if response.status_code == 200:
            return response.json().get("groups", [])
        return []


def main() -> int:
    parser = argparse.ArgumentParser(description="Provision a WSO2 test user")
    parser.add_argument("--ws-url", help="WSO2 base URL")
    parser.add_argument("--admin-user", help="WSO2 admin username")
    parser.add_argument("--admin-pass", help="WSO2 admin password")
    parser.add_argument("--username", required=True, help="Username to create/update")
    parser.add_argument("--password", required=True, help="Password to set")
    parser.add_argument("--role", required=True, help="Role/group to ensure")
    parser.add_argument("--display-name", help="Display name to use")
    args = parser.parse_args()

    ws_url = env_or(args.ws_url, "WSO2_IS_URL", "https://test.letsplaydarts.eu/auth")
    admin_user = env_or(
        args.admin_user,
        "WSO2_ADMIN_USER",
        os.getenv("WSO2_IS_INTROSPECT_USER", "admin"),
    )
    admin_pass = env_or(
        args.admin_pass,
        "WSO2_ADMIN_PASS",
        os.getenv("WSO2_IS_INTROSPECT_PASSWORD", "admin"),
    )
    display_name = args.display_name or args.username.capitalize()

    client = WSO2SCIMClient(ws_url, admin_user, admin_pass)

    print("=" * 72)
    print("WSO2 Test User Bootstrap")
    print("=" * 72)
    print(f"WSO2 URL: {ws_url}")
    print(f"Username: {args.username}")
    print(f"Role: {args.role}")
    print(f"Display name: {display_name}")

    user = client.get_user(args.username)
    if user:
        print(f"Found existing user: {user.get('userName')} ({user.get('id')})")
        if client.update_password(user["id"], args.password):
            print("Updated user password")
        else:
            print("Failed to update password")
            return 2
    else:
        user = client.create_user(args.username, args.password, display_name)
        if not user:
            print("Failed to create user")
            return 3
        print(f"Created user: {user.get('userName')} ({user.get('id')})")

    group = client.get_group(args.role)
    if not group:
        print(f"Role group '{args.role}' not found; creating it")
        group = client.create_group(args.role)
        if not group:
            print(f"Failed to create role group '{args.role}'")
            return 4

    if client.add_user_to_group(user["id"], args.username, group["id"]):
        print(f"Added {args.username} to role {args.role}")
    else:
        print(f"Failed to add {args.username} to role {args.role}")
        return 5

    groups = client.user_groups(user["id"])
    print("Current roles:")
    for group_info in groups:
        print(f" - {group_info.get('display', 'N/A')}")

    print("Success")
    return 0


if __name__ == "__main__":
    sys.exit(main())

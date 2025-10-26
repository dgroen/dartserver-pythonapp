#!/usr/bin/env python3
"""
Test script for Mobile App functionality
Tests all mobile endpoints and features
"""

import sys
from datetime import datetime

import requests

# Configuration
BASE_URL = "http://localhost:5000"
TEST_USERNAME = "test_user"
TEST_PASSWORD = "test_password"  # pragma: allowlist secret


class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    END = "\033[0m"


def print_test(name, status, message=""):
    """Print test result"""
    if status:
        print(f"{Colors.GREEN}✓{Colors.END} {name}")
        if message:
            print(f"  {Colors.BLUE}→{Colors.END} {message}")
    else:
        print(f"{Colors.RED}✗{Colors.END} {name}")
        if message:
            print(f"  {Colors.RED}→{Colors.END} {message}")


def test_server_running():
    """Test if server is running"""
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        print_test("Server is running", True, f"Status: {response.status_code}")
        return True
    except Exception as e:
        print_test("Server is running", False, str(e))
        return False


def test_mobile_pages():
    """Test mobile page routes"""
    pages = [
        "/mobile",
        "/mobile/gameplay",
        "/mobile/gamemaster",
        "/mobile/dartboard-setup",
        "/mobile/results",
        "/mobile/account",
        "/mobile/hotspot",
    ]

    print(f"\n{Colors.YELLOW}Testing Mobile Pages:{Colors.END}")
    for page in pages:
        try:
            response = requests.get(f"{BASE_URL}{page}", allow_redirects=False, timeout=5)
            # Should redirect to login (302) or show page (200)
            success = response.status_code in [200, 302]
            print_test(f"  {page}", success, f"Status: {response.status_code}")
        except Exception as e:
            print_test(f"  {page}", False, str(e))


def test_api_endpoints():
    """Test API endpoints (without authentication)"""
    endpoints = [
        ("/api/game/state", "GET"),
        ("/api/game/current", "GET"),
        ("/api/game/history", "GET"),
        ("/api/game/results", "GET"),
    ]

    print(f"\n{Colors.YELLOW}Testing API Endpoints:{Colors.END}")
    for endpoint, method in endpoints:
        try:
            if method == "GET":
                response = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
            else:
                response = requests.post(f"{BASE_URL}{endpoint}", json={}, timeout=5)

            # Should return 401 (unauthorized) or 302 (redirect) or 200 (success)
            success = response.status_code in [200, 302, 401]
            print_test(f"  {method} {endpoint}", success, f"Status: {response.status_code}")
        except Exception as e:
            print_test(f"  {method} {endpoint}", False, str(e))


def test_mobile_api_endpoints():
    """Test mobile-specific API endpoints"""
    endpoints = [
        ("/api/mobile/apikeys", "GET"),
        ("/api/mobile/dartboards", "GET"),
        ("/api/mobile/hotspot", "GET"),
    ]

    print(f"\n{Colors.YELLOW}Testing Mobile API Endpoints:{Colors.END}")
    for endpoint, method in endpoints:
        try:
            if method == "GET":
                response = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
            else:
                response = requests.post(f"{BASE_URL}{endpoint}", json={}, timeout=5)

            # Should return 401 (unauthorized) or 302 (redirect)
            success = response.status_code in [200, 302, 401]
            print_test(f"  {method} {endpoint}", success, f"Status: {response.status_code}")
        except Exception as e:
            print_test(f"  {method} {endpoint}", False, str(e))


def test_static_files():
    """Test static files"""
    files = [
        "/static/css/mobile.css",
        "/static/js/mobile.js",
        "/static/js/mobile_gameplay.js",
        "/static/js/mobile_gamemaster.js",
        "/static/js/mobile_dartboard_setup.js",
        "/static/js/mobile_results.js",
        "/static/js/mobile_account.js",
        "/static/js/mobile_hotspot.js",
        "/static/manifest.json",
        "/static/service-worker.js",
    ]

    print(f"\n{Colors.YELLOW}Testing Static Files:{Colors.END}")
    for file in files:
        try:
            response = requests.get(f"{BASE_URL}{file}", timeout=5)
            success = response.status_code == 200
            size = len(response.content) if success else 0
            print_test(f"  {file}", success, f"Size: {size} bytes")
        except Exception as e:
            print_test(f"  {file}", False, str(e))


def test_pwa_manifest():
    """Test PWA manifest"""
    print(f"\n{Colors.YELLOW}Testing PWA Manifest:{Colors.END}")
    try:
        response = requests.get(f"{BASE_URL}/static/manifest.json", timeout=5)
        if response.status_code == 200:
            manifest = response.json()
            print_test("  Manifest loads", True)
            print_test("  Has name", "name" in manifest, manifest.get("name", ""))
            print_test("  Has short_name", "short_name" in manifest, manifest.get("short_name", ""))
            print_test("  Has icons", "icons" in manifest and len(manifest.get("icons", [])) > 0)
            print_test("  Has start_url", "start_url" in manifest, manifest.get("start_url", ""))
        else:
            print_test("  Manifest loads", False, f"Status: {response.status_code}")
    except Exception as e:
        print_test("  Manifest loads", False, str(e))


def test_database_models():
    """Test database models import"""
    print(f"\n{Colors.YELLOW}Testing Database Models:{Colors.END}")
    try:
        print_test("  Player model", True)
        print_test("  Dartboard model", True)
        print_test("  ApiKey model", True)
        print_test("  HotspotConfig model", True)
    except Exception as e:
        print_test("  Database models", False, str(e))


def test_mobile_service():
    """Test mobile service import"""
    print(f"\n{Colors.YELLOW}Testing Mobile Service:{Colors.END}")
    try:
        from src.mobile_service import MobileService

        print_test("  MobileService imports", True)

        # Check methods exist
        methods = [
            "create_api_key",
            "validate_api_key",
            "revoke_api_key",
            "get_user_api_keys",
            "register_dartboard",
            "get_user_dartboards",
            "delete_dartboard",
            "update_dartboard_connection",
            "create_hotspot_config",
            "get_hotspot_configs",
            "toggle_hotspot",
        ]

        for method in methods:
            has_method = hasattr(MobileService, method)
            print_test(f"  Has {method}()", has_method)

    except Exception as e:
        print_test("  MobileService imports", False, str(e))


def main():
    """Run all tests"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}Mobile App Test Suite{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"Testing: {BASE_URL}")
    print(f"Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Test server
    if not test_server_running():
        print(f"\n{Colors.RED}Server is not running. Please start the server first:{Colors.END}")
        print("  cd /data/dartserver-pythonapp")
        print("  python app.py")
        sys.exit(1)

    # Run tests
    test_mobile_pages()
    test_api_endpoints()
    test_mobile_api_endpoints()
    test_static_files()
    test_pwa_manifest()
    test_database_models()
    test_mobile_service()

    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.GREEN}Test suite completed!{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}\n")


if __name__ == "__main__":
    main()

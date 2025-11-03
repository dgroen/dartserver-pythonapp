#!/usr/bin/env python3
"""
Mobile App API Examples

This script demonstrates how to interact with the mobile app API
for dartboard connectivity, game management, and score submission.

Requirements:
- Server running on localhost:5000
- Valid session cookie or API key
- Database configured and migrated
"""

import json
import sys
from datetime import datetime

import requests

# Configuration
BASE_URL = "http://localhost:5000"
SESSION_COOKIE = None  # Will be set after login
API_KEY = None  # Will be set after API key creation


class Colors:
    """ANSI color codes for terminal output"""

    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    END = "\033[0m"


def print_section(title):
    """Print a section header"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'=' * 60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{title}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'=' * 60}{Colors.END}\n")


def print_success(message):
    """Print success message"""
    print(f"{Colors.GREEN}✓{Colors.END} {message}")


def print_error(message):
    """Print error message"""
    print(f"{Colors.RED}✗{Colors.END} {message}")


def print_info(message):
    """Print info message"""
    print(f"{Colors.BLUE}ℹ{Colors.END} {message}")


def print_json(data):
    """Pretty print JSON data"""
    print(f"{Colors.YELLOW}{json.dumps(data, indent=2)}{Colors.END}")


def test_server_health():
    """Test if server is accessible"""
    print_section("1. Server Health Check")

    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print_success(f"Server is running at {BASE_URL}")
            return True
        else:
            print_error(f"Server returned status code {response.status_code}")
            return False
    except requests.RequestException as e:
        print_error(f"Cannot connect to server: {e}")
        print_info("Make sure the server is running: python run.py")
        return False


def test_mobile_pages():
    """Test mobile page accessibility"""
    print_section("2. Mobile Pages Accessibility")

    pages = [
        ("/mobile", "Mobile Home"),
        ("/mobile/gameplay", "Gameplay"),
        ("/mobile/gamemaster", "Game Master"),
        ("/mobile/dartboard-setup", "Dartboard Setup"),
        ("/mobile/results", "Results"),
        ("/mobile/account", "Account"),
        ("/mobile/hotspot", "Hotspot Control"),
    ]

    all_accessible = True
    for path, name in pages:
        try:
            response = requests.get(f"{BASE_URL}{path}", timeout=5, allow_redirects=False)
            # Page may redirect to login if not authenticated
            if response.status_code in [200, 302]:
                print_success(f"{name:20} - Accessible ({response.status_code})")
            else:
                print_error(f"{name:20} - Status {response.status_code}")
                all_accessible = False
        except requests.RequestException as e:
            print_error(f"{name:20} - Error: {e}")
            all_accessible = False

    return all_accessible


def test_pwa_resources():
    """Test PWA resources (manifest, service worker, icons)"""
    print_section("3. PWA Resources")

    resources = [
        ("/static/manifest.json", "PWA Manifest"),
        ("/static/service-worker.js", "Service Worker"),
        ("/static/icons/icon-192x192.png", "Icon 192x192"),
        ("/static/icons/icon-512x512.png", "Icon 512x512"),
    ]

    all_available = True
    for path, name in resources:
        try:
            response = requests.get(f"{BASE_URL}{path}", timeout=5)
            if response.status_code == 200:
                size = len(response.content)
                print_success(f"{name:20} - Available ({size} bytes)")
            else:
                print_error(f"{name:20} - Status {response.status_code}")
                all_available = False
        except requests.RequestException as e:
            print_error(f"{name:20} - Error: {e}")
            all_available = False

    return all_available


def test_api_endpoints_unauthenticated():
    """Test API endpoints without authentication (should fail)"""
    print_section("4. API Endpoints (Unauthenticated)")

    print_info("These should return 401 or 302 (redirect to login)")

    endpoints = [
        ("GET", "/api/mobile/apikeys", "List API Keys"),
        ("GET", "/api/mobile/dartboards", "List Dartboards"),
        ("GET", "/api/game/current", "Current Game"),
    ]

    for method, path, name in endpoints:
        try:
            response = None
            if method == "GET":
                response = requests.get(f"{BASE_URL}{path}", timeout=5, allow_redirects=False)
            elif method == "POST":
                response = requests.post(f"{BASE_URL}{path}", timeout=5, allow_redirects=False)
            else:
                print_error(f"{name:25} - Unsupported method {method}")
                continue

            if response and response.status_code in [401, 302, 403]:
                print_success(f"{name:25} - Properly secured ({response.status_code})")
            elif response:
                print_error(f"{name:25} - Unexpected status {response.status_code}")
        except requests.RequestException as e:
            print_error(f"{name:25} - Error: {e}")


def test_manifest_configuration():
    """Test and display PWA manifest configuration"""
    print_section("5. PWA Manifest Configuration")

    try:
        response = requests.get(f"{BASE_URL}/static/manifest.json", timeout=5)
        if response.status_code == 200:
            manifest = response.json()
            print_success("Manifest loaded successfully")
            print_info(f"App Name: {manifest.get('name', 'N/A')}")
            print_info(f"Short Name: {manifest.get('short_name', 'N/A')}")
            print_info(f"Start URL: {manifest.get('start_url', 'N/A')}")
            print_info(f"Display Mode: {manifest.get('display', 'N/A')}")
            print_info(f"Theme Color: {manifest.get('theme_color', 'N/A')}")
            print_info(f"Icons: {len(manifest.get('icons', []))} sizes")
            print_info(f"Shortcuts: {len(manifest.get('shortcuts', []))} shortcuts")

            print("\n" + Colors.YELLOW + "Full Manifest:" + Colors.END)
            print_json(manifest)
            return True
        else:
            print_error(f"Failed to load manifest (status {response.status_code})")
            return False
    except requests.RequestException as e:
        print_error(f"Error loading manifest: {e}")
        return False


def test_service_worker():
    """Test service worker file"""
    print_section("6. Service Worker")

    try:
        response = requests.get(f"{BASE_URL}/static/service-worker.js", timeout=5)
        if response.status_code == 200:
            content = response.text
            print_success(f"Service worker loaded ({len(content)} bytes)")

            # Check for important features
            if "CACHE_NAME" in content:
                print_info("✓ Cache versioning implemented")
            if "install" in content:
                print_info("✓ Install event handler present")
            if "fetch" in content:
                print_info("✓ Fetch event handler present")
            if "activate" in content:
                print_info("✓ Activate event handler present")

            # Extract cache name
            import re

            cache_match = re.search(r"CACHE_NAME\s*=\s*['\"]([^'\"]+)['\"]", content)
            if cache_match:
                print_info(f"Cache name: {cache_match.group(1)}")

            return True
        else:
            print_error(f"Failed to load service worker (status {response.status_code})")
            return False
    except requests.RequestException as e:
        print_error(f"Error loading service worker: {e}")
        return False


def example_api_key_usage():
    """Example: How to use API keys for dartboard authentication"""
    print_section("7. API Key Usage Example")

    print_info("To create and use an API key:")
    print()
    print(f"{Colors.YELLOW}1. Login to the mobile app:{Colors.END}")
    print(f"   Open {BASE_URL}/mobile")
    print(f"   Login with your credentials")
    print()
    print(f"{Colors.YELLOW}2. Navigate to Account page:{Colors.END}")
    print(f"   {BASE_URL}/mobile/account")
    print()
    print(f"{Colors.YELLOW}3. Create API key:{Colors.END}")
    print("   Click 'Create New API Key'")
    print("   Enter a name (e.g., 'My Dartboard')")
    print("   Copy the generated key (shown only once!)")
    print()
    print(f"{Colors.YELLOW}4. Use the API key to submit scores:{Colors.END}")
    print()
    print(f"{Colors.CYAN}Example curl command:{Colors.END}")
    print()
    print(
        """    curl -X POST http://localhost:5000/api/score \\
      -H "Content-Type: application/json" \\
      -H "X-API-Key: your-api-key-here" \\
      -d '{
        "score": 20,
        "multiplier": "TRIPLE"
      }'"""
    )
    print()
    print(f"{Colors.CYAN}Example Python code:{Colors.END}")
    print()
    print(
        """    import requests

    response = requests.post(
        'http://localhost:5000/api/score',
        headers={
            'Content-Type': 'application/json',
            'X-API-Key': 'your-api-key-here'
        },
        json={
            'score': 20,
            'multiplier': 'TRIPLE'
        }
    )

    print(response.json())"""
    )


def example_dartboard_registration():
    """Example: How to register a dartboard"""
    print_section("8. Dartboard Registration Example")

    print_info("To register a dartboard:")
    print()
    print(f"{Colors.YELLOW}1. Navigate to Dartboard Setup:{Colors.END}")
    print(f"   {BASE_URL}/mobile/dartboard-setup")
    print()
    print(f"{Colors.YELLOW}2. Fill in the form:{Colors.END}")
    print("   - Dartboard ID: DART-ABC123 (unique identifier)")
    print("   - Dartboard Name: Living Room Dartboard")
    print("   - WPA Key: your-secure-key (for hotspot)")
    print()
    print(f"{Colors.YELLOW}3. Submit the form{Colors.END}")
    print()
    print(f"{Colors.CYAN}Or use the API:{Colors.END}")
    print()
    print(
        """    curl -X POST http://localhost:5000/api/mobile/dartboards \\
      -H "Content-Type: application/json" \\
      -H "Cookie: session=your-session-cookie" \\
      -d '{
        "dartboard_id": "DART-ABC123",
        "name": "Living Room Dartboard",
        "wpa_key": "your-secure-key"
      }'"""
    )


def example_hotspot_setup():
    """Example: How to setup mobile hotspot"""
    print_section("9. Mobile Hotspot Setup Example")

    print_info("Setting up mobile hotspot for dartboard connectivity:")
    print()
    print(f"{Colors.YELLOW}Android:{Colors.END}")
    print("   1. Go to Settings → Network & Internet → Hotspot & tethering")
    print("   2. Tap 'Wi-Fi hotspot'")
    print("   3. Set hotspot name to your dartboard ID (e.g., DART-ABC123)")
    print("   4. Set password to your WPA key")
    print("   5. Turn on hotspot")
    print()
    print(f"{Colors.YELLOW}iOS:{Colors.END}")
    print("   1. Go to Settings → Personal Hotspot")
    print("   2. Turn on 'Allow Others to Join'")
    print("   3. Set password to your WPA key")
    print("   4. Note: iOS doesn't allow custom SSID")
    print()
    print(f"{Colors.YELLOW}After hotspot is active:{Colors.END}")
    print("   - Your dartboard will automatically connect")
    print("   - Scores will be sent to the app in real-time")
    print("   - View scores on the Gameplay page")


def run_all_tests():
    """Run all tests and examples"""
    print(f"\n{Colors.BOLD}{Colors.GREEN}🎯 Mobile App API Examples and Tests{Colors.END}\n")
    print(f"Testing server at: {Colors.BOLD}{BASE_URL}{Colors.END}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    results = {}

    # Run tests
    results["health"] = test_server_health()

    if not results["health"]:
        print_error("\nServer is not accessible. Exiting.")
        sys.exit(1)

    results["pages"] = test_mobile_pages()
    results["pwa_resources"] = test_pwa_resources()
    test_api_endpoints_unauthenticated()
    results["manifest"] = test_manifest_configuration()
    results["service_worker"] = test_service_worker()

    # Show examples
    example_api_key_usage()
    example_dartboard_registration()
    example_hotspot_setup()

    # Summary
    print_section("Summary")

    total_tests = len(results)
    passed_tests = sum(1 for v in results.values() if v)

    if passed_tests == total_tests:
        print_success(f"All {total_tests} tests passed! 🎉")
    else:
        print_error(f"{passed_tests}/{total_tests} tests passed")

    print()
    print(f"{Colors.BOLD}Next Steps:{Colors.END}")
    print("  1. Start the server: python run.py")
    print(f"  2. Open mobile app: {BASE_URL}/mobile")
    print("  3. Login with your credentials")
    print("  4. Explore the mobile features!")
    print()
    print(f"{Colors.BOLD}Documentation:{Colors.END}")
    print("  - Complete mobile app guide: MOBILE_APP.md")
    print("  - Quick start: docs/MOBILE_APP_QUICKSTART.md")
    print("  - Deployment: docs/MOBILE_APP_DEPLOYMENT.md")
    print()

    return passed_tests == total_tests


if __name__ == "__main__":
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Test interrupted by user{Colors.END}")
        sys.exit(130)
    except Exception as e:
        print(f"\n{Colors.RED}Unexpected error: {e}{Colors.END}")
        import traceback

        traceback.print_exc()
        sys.exit(1)

#!/usr/bin/env python3
"""Test script to validate Swagger documentation syntax"""

import sys

# Import the app to test
sys.path.insert(0, "/data/dartserver-pythonapp")

try:
    # Try to import and initialize the app
    from app import app

    print("✓ App imported successfully")
    print("✓ Swagger initialized successfully")

    # Try to get the API spec
    with app.test_client() as client:
        response = client.get("/apispec.json")
        print(f"\nAPI Spec Status Code: {response.status_code}")

        if response.status_code == 200:
            spec = response.get_json()
            print("✓ API spec generated successfully")
            print(f"  Title: {spec.get('info', {}).get('title')}")
            print(f"  Version: {spec.get('info', {}).get('version')}")
            print(f"  Endpoints: {len(spec.get('paths', {}))}")
            print("\nEndpoints:")
            for path in sorted(spec.get("paths", {}).keys()):
                methods = list(spec["paths"][path].keys())
                print(f"  {path}: {', '.join(methods)}")
        else:
            print("✗ Failed to generate API spec")
            print(f"  Response: {response.get_data(as_text=True)[:500]}")

except Exception as e:
    print(f"✗ Error: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)

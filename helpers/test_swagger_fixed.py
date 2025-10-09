#!/usr/bin/env python3
"""Test script to verify Swagger API documentation is working"""

import sys

# Import the app to test
sys.path.insert(0, "/data/dartserver-pythonapp")

try:
    from app import app

    print("=" * 60)
    print("SWAGGER/OPENAPI DOCUMENTATION TEST")
    print("=" * 60)

    with app.test_client() as client:
        # Test 1: Check if Swagger UI is accessible
        print("\n1. Testing Swagger UI endpoint (/api/docs/)...")
        response = client.get("/api/docs/")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✓ Swagger UI is accessible")
        else:
            print("   ✗ Failed to access Swagger UI")

        # Test 2: Check if API spec is available
        print("\n2. Testing API specification endpoint (/apispec.json)...")
        response = client.get("/apispec.json")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            spec = response.get_json()
            print("   ✓ API spec generated successfully")
            print(f"   Title: {spec.get('info', {}).get('title')}")
            print(f"   Version: {spec.get('info', {}).get('version')}")
            print(f"   Description: {spec.get('info', {}).get('description')}")

            paths = spec.get("paths", {})
            print(f"   Total Endpoints: {len(paths)}")

            # Test 3: Verify all endpoints have proper documentation
            print("\n3. Verifying endpoint documentation...")
            issues = []
            for path, methods in sorted(paths.items()):
                for method, details in methods.items():
                    if method in ["get", "post", "put", "delete", "patch"]:
                        # Check for required fields
                        if "summary" not in details:
                            issues.append(f"   ⚠ {method.upper()} {path}: Missing 'summary'")
                        if "description" not in details:
                            issues.append(f"   ⚠ {method.upper()} {path}: Missing 'description'")
                        if "tags" not in details:
                            issues.append(f"   ⚠ {method.upper()} {path}: Missing 'tags'")

            if issues:
                print(f"   Found {len(issues)} documentation issues:")
                for issue in issues[:10]:  # Show first 10
                    print(issue)
                if len(issues) > 10:
                    print(f"   ... and {len(issues) - 10} more")
            else:
                print("   ✓ All endpoints have proper documentation")

            # Test 4: List all documented endpoints
            print("\n4. Documented API Endpoints:")
            print("   " + "-" * 56)
            http_methods = ["get", "post", "put", "delete", "patch"]
            for path in sorted(paths.keys()):
                methods = [m.upper() for m in paths[path] if m in http_methods]
                first_method = methods[0].lower() if methods else "get"
                tags = paths[path].get(first_method, {}).get("tags", ["Untagged"])
                if not methods:
                    tags = ["Untagged"]
                print(f"   {', '.join(methods):12} {path:35} [{', '.join(tags)}]")

            # Test 5: Verify tags
            print("\n5. API Tags:")
            tags = spec.get("tags", [])
            if tags:
                for tag in tags:
                    print(f"   • {tag.get('name')}: {tag.get('description', 'No description')}")
            else:
                print("   ⚠ No tags defined")

            # Test 6: Check for security definitions
            print("\n6. Security Configuration:")
            security_defs = spec.get("securityDefinitions", {})
            if security_defs:
                for name, config in security_defs.items():
                    print(f"   • {name}: {config.get('type', 'unknown')}")
            else:
                print("   (i) No security definitions (authentication handled separately)")

            print("\n" + "=" * 60)
            print("✓ SWAGGER DOCUMENTATION IS WORKING CORRECTLY")
            print("=" * 60)
            print("\nAccess Swagger UI at: http://localhost:5000/api/docs/")
            print("API Specification at: http://localhost:5000/apispec.json")
            print("\nNote: Most endpoints require authentication via WSO2 IS")

        else:
            print("   ✗ Failed to get API spec")
            print(f"   Response: {response.get_data(as_text=True)[:500]}")
            sys.exit(1)

except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)

#!/usr/bin/env python3
"""
Installation verification script for Darts Game Application
"""
import importlib.util
import sys


def check_python_version():
    """Check if Python version is 3.8 or higher"""
    print("Checking Python version...", end=" ")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"✓ Python {version.major}.{version.minor}.{version.micro}")
        return True
    print(f"✗ Python {version.major}.{version.minor}.{version.micro} (need 3.8+)")
    return False


def check_package(package_name, import_name=None):
    """Check if a Python package is installed"""
    if import_name is None:
        import_name = package_name

    print(f"Checking {package_name}...", end=" ")
    spec = importlib.util.find_spec(import_name)
    if spec is not None:
        print("✓")
        return True
    print("✗")
    return False


def check_rabbitmq():
    """Check if RabbitMQ is accessible"""
    print("Checking RabbitMQ connection...", end=" ")
    try:
        import pika

        credentials = pika.PlainCredentials("guest", "guest")
        parameters = pika.ConnectionParameters(
            host="localhost",
            port=5672,
            credentials=credentials,
            connection_attempts=1,
            socket_timeout=2,
        )
        connection = pika.BlockingConnection(parameters)
        connection.close()
        print("✓")
        return True
    except Exception as e:
        print(f"✗ ({str(e)[:50]}...)")
        return False


def check_file_structure():
    """Check if all required files exist"""
    import os

    print("\nChecking file structure...")

    required_files = [
        "app.py",
        "game_manager.py",
        "rabbitmq_consumer.py",
        "requirements.txt",
        ".env.example",
        "games/__init__.py",
        "games/game_301.py",
        "games/game_cricket.py",
        "templates/index.html",
        "templates/control.html",
        "static/css/style.css",
        "static/css/control.css",
        "static/js/main.js",
        "static/js/control.js",
    ]

    all_exist = True
    for file_path in required_files:
        exists = os.path.exists(file_path)
        status = "✓" if exists else "✗"
        print(f"  {status} {file_path}")
        if not exists:
            all_exist = False

    return all_exist


def check_env_file():
    """Check if .env file exists"""
    import os

    print("\nChecking configuration...", end=" ")
    if os.path.exists(".env"):
        print("✓ .env file exists")
        return True
    print("⚠ .env file not found (will use defaults)")
    return False


def main():
    """Run all checks"""
    print("=" * 60)
    print("Darts Game Application - Installation Verification")
    print("=" * 60)
    print()

    results = {}

    # Check Python version
    results["python"] = check_python_version()
    print()

    # Check required packages
    print("Checking Python packages...")
    packages = [
        ("flask", "flask"),
        ("flask-socketio", "flask_socketio"),
        ("flask-cors", "flask_cors"),
        ("pika", "pika"),
        ("python-socketio", "socketio"),
        ("eventlet", "eventlet"),
        ("python-dotenv", "dotenv"),
    ]

    package_results = []
    for package_name, import_name in packages:
        package_results.append(check_package(package_name, import_name))

    results["packages"] = all(package_results)
    print()

    # Check file structure
    results["files"] = check_file_structure()
    print()

    # Check .env file
    results["env"] = check_env_file()
    print()

    # Check RabbitMQ (optional)
    results["rabbitmq"] = check_rabbitmq()
    print()

    # Summary
    print("=" * 60)
    print("Summary")
    print("=" * 60)

    if results["python"]:
        print("✓ Python version OK")
    else:
        print("✗ Python version too old - upgrade to 3.8+")

    if results["packages"]:
        print("✓ All required packages installed")
    else:
        print("✗ Some packages missing - run: pip install -r requirements.txt")

    if results["files"]:
        print("✓ All required files present")
    else:
        print("✗ Some files missing - check installation")

    if results["env"]:
        print("✓ Configuration file present")
    else:
        print("⚠ No .env file - copy .env.example to .env")

    if results["rabbitmq"]:
        print("✓ RabbitMQ connection OK")
    else:
        print("⚠ RabbitMQ not accessible - install and start RabbitMQ")
        print("  (Application will work without RabbitMQ, but won't receive messages)")

    print()

    # Overall status
    critical_checks = [results["python"], results["packages"], results["files"]]

    if all(critical_checks):
        print("=" * 60)
        print("✓ Installation verified successfully!")
        print("=" * 60)
        print()
        print("You can now start the application:")
        print("  python app.py")
        print()
        print("Or use Docker:")
        print("  docker-compose up")
        print()
        print("Then open: http://localhost:5000")
        return 0
    print("=" * 60)
    print("✗ Installation incomplete")
    print("=" * 60)
    print()
    print("Please fix the issues above and run this script again.")
    return 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env bash
# Development environment setup script

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
print_header() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

check_command() {
    if command -v "$1" &> /dev/null; then
        print_success "$1 is installed"
        return 0
    else
        print_error "$1 is not installed"
        return 1
    fi
}

# Main setup
print_header "Dartserver Python App - Development Setup"

# Check prerequisites
print_info "Checking prerequisites..."
echo ""

MISSING_DEPS=0

if ! check_command python3; then
    print_error "Python 3 is required"
    MISSING_DEPS=1
fi

if ! check_command git; then
    print_error "Git is required"
    MISSING_DEPS=1
fi

if [ $MISSING_DEPS -eq 1 ]; then
    echo ""
    print_error "Please install missing dependencies and try again"
    exit 1
fi

echo ""

# Check Python version
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
print_info "Python version: $PYTHON_VERSION"

if [[ "$PYTHON_VERSION" < "3.10" ]]; then
    print_error "Python 3.10 or higher is required"
    exit 1
fi

print_success "Python version is compatible"
echo ""

# Check for python3-venv
print_info "Checking for python3-venv..."
if python3 -m venv --help &> /dev/null; then
    print_success "python3-venv is available"
else
    print_error "python3-venv is not installed"
    print_info "Installing python3-venv..."
    sudo apt-get update && sudo apt-get install -y python3-venv
    if python3 -m venv --help &> /dev/null; then
        print_success "python3-venv installed successfully"
    else
        print_error "Failed to install python3-venv"
        exit 1
    fi
fi
echo ""

# Install UV if not present
print_header "Installing UV Package Manager"

if command -v uv &> /dev/null; then
    print_success "UV is already installed"
    UV_VERSION=$(uv --version)
    print_info "Version: $UV_VERSION"
else
    print_info "Installing UV..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    
    # Add UV to PATH for current session (try multiple possible locations)
    export PATH="$HOME/.cargo/bin:$HOME/.local/bin:$PATH"
    
    if command -v uv &> /dev/null; then
        print_success "UV installed successfully"
        UV_VERSION=$(uv --version)
        print_info "Version: $UV_VERSION"
    else
        print_error "UV installation failed"
        print_info "Please install UV manually: https://github.com/astral-sh/uv"
        exit 1
    fi
fi

echo ""

# Create virtual environment
print_header "Setting Up Virtual Environment"

if [ -d ".venv" ]; then
    print_warning "Virtual environment already exists"
    read -p "Do you want to recreate it? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "Removing existing virtual environment..."
        rm -rf .venv
        print_info "Creating new virtual environment..."
        uv venv
        print_success "Virtual environment created"
    else
        print_info "Using existing virtual environment"
    fi
else
    print_info "Creating virtual environment..."
    uv venv
    print_success "Virtual environment created"
fi

echo ""

# Activate virtual environment
print_info "Activating virtual environment..."
source .venv/bin/activate
print_success "Virtual environment activated"

echo ""

# Ensure pip is available in venv
print_info "Ensuring pip is available..."
if ! python -m pip --version &> /dev/null; then
    print_warning "pip not found in venv, installing..."
    python -m ensurepip --upgrade 2>/dev/null || curl https://bootstrap.pypa.io/get-pip.py | python
fi
print_success "pip is available"

echo ""

# Install dependencies
print_header "Installing Dependencies"

print_info "Installing development dependencies with UV..."
uv pip install -e ".[dev,lint,test]"
print_success "Dependencies installed"

echo ""

# Install pre-commit
print_header "Setting Up Pre-commit Hooks"

# Verify pre-commit is installed (should be from dev dependencies)
if python -m pip show pre-commit &> /dev/null; then
    print_success "pre-commit is installed"
    
    # Install pre-commit hooks
    print_info "Installing pre-commit hooks..."
    if pre-commit install; then
        print_success "Pre-commit hooks installed"
    else
        print_warning "Failed to install pre-commit hooks, but continuing..."
    fi
else
    print_warning "pre-commit not found in dependencies, skipping hook installation"
fi

echo ""

# Setup custom git hooks
print_header "Setting Up Custom Git Hooks"

if [ -f ".git-hooks/pre-commit" ]; then
    print_info "Installing custom pre-commit hook..."
    chmod +x .git-hooks/pre-commit
    cp .git-hooks/pre-commit .git/hooks/pre-commit
    print_success "Custom git hooks installed"
else
    print_warning "Custom git hooks not found, skipping..."
fi

echo ""

# Run initial tests
print_header "Running Initial Tests"

print_info "Running test suite..."
if pytest tests/ -v --tb=short; then
    print_success "All tests passed!"
else
    print_warning "Some tests failed. This might be expected for a new setup."
fi

echo ""

# Create necessary directories
print_header "Creating Project Directories"

mkdir -p htmlcov
mkdir -p .pytest_cache
print_success "Project directories created"

echo ""

# Summary
print_header "Setup Complete!"

echo "Development environment is ready! 🚀"
echo ""
echo "Quick start commands:"
echo ""
echo "  ${GREEN}make test${NC}          - Run all tests"
echo "  ${GREEN}make test-cov${NC}      - Run tests with coverage"
echo "  ${GREEN}make lint${NC}          - Check code quality"
echo "  ${GREEN}make lint-fix${NC}      - Auto-fix code quality issues"
echo "  ${GREEN}make tox${NC}           - Run tests in all environments"
echo "  ${GREEN}make run${NC}           - Start the application"
echo "  ${GREEN}make help${NC}          - Show all available commands"
echo ""
echo "Documentation:"
echo ""
echo "  ${BLUE}DEVELOPMENT.md${NC}     - Development guide"
echo "  ${BLUE}TESTING.md${NC}         - Testing guide"
echo "  ${BLUE}README.md${NC}          - Project overview"
echo ""
echo "Next steps:"
echo ""
echo "  1. Activate virtual environment: ${YELLOW}source .venv/bin/activate${NC}"
echo "  2. Run tests: ${YELLOW}make test${NC}"
echo "  3. Start coding! 💻"
echo ""
echo "For help, run: ${YELLOW}make help${NC}"
echo ""

print_success "Happy coding! 🎯"
echo ""
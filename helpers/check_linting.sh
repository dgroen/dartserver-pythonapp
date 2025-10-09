#!/bin/bash
# Comprehensive linting check script for Dartserver Python App

set -e

echo "🎯 Dartserver Python App - Linting Check"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track overall status
OVERALL_STATUS=0

# Function to run a linter and report status
run_linter() {
    local name=$1
    local command=$2
    
    echo -n "Checking $name... "
    
    if eval "$command" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ PASSED${NC}"
        return 0
    else
        echo -e "${RED}❌ FAILED${NC}"
        return 1
    fi
}

# Change to project directory
cd /data/dartserver-pythonapp

# Activate virtual environment
source .venv/bin/activate

echo "Running primary linters..."
echo ""

# Ruff
if run_linter "Ruff" ".venv/bin/ruff check ."; then
    :
else
    OVERALL_STATUS=1
    echo "  Run: ruff check --fix . (to auto-fix)"
fi

# Flake8
if run_linter "Flake8" ".venv/bin/flake8 ."; then
    :
else
    OVERALL_STATUS=1
fi

# Black
if run_linter "Black" ".venv/bin/black --check ."; then
    :
else
    OVERALL_STATUS=1
    echo "  Run: black . (to auto-format)"
fi

# isort
if run_linter "isort" ".venv/bin/isort --check-only . --skip .venv --skip venv --skip .tox --skip build"; then
    :
else
    OVERALL_STATUS=1
    echo "  Run: isort . --skip .venv (to auto-sort imports)"
fi

echo ""
echo "=========================================="

if [ $OVERALL_STATUS -eq 0 ]; then
    echo -e "${GREEN}✅ ALL PRIMARY LINTERS PASSED!${NC}"
    echo ""
    echo "Optional checks (informational only):"
    echo ""
    
    # Pylint (informational)
    echo -n "Checking Pylint (informational)... "
    PYLINT_OUTPUT=$(.venv/bin/pylint --rcfile=pyproject.toml $(find . -name "*.py" -not -path "./.venv/*" -not -path "./venv/*" -not -path "./.tox/*" -not -path "./build/*") 2>&1 | grep -c "^[EWC]:" || true)
    if [ "$PYLINT_OUTPUT" -eq 0 ]; then
        echo -e "${GREEN}✅ No issues${NC}"
    else
        echo -e "${YELLOW}⚠️  $PYLINT_OUTPUT warnings (acceptable)${NC}"
    fi
    
    # Mypy (informational)
    echo -n "Checking Mypy (informational)... "
    MYPY_OUTPUT=$(.venv/bin/mypy . --exclude '.venv|venv|.tox|build' 2>&1 | grep -c "error:" || true)
    if [ "$MYPY_OUTPUT" -eq 0 ]; then
        echo -e "${GREEN}✅ No issues${NC}"
    else
        echo -e "${YELLOW}⚠️  $MYPY_OUTPUT type hints (acceptable)${NC}"
    fi
    
    echo ""
    echo "🎉 Codebase is ready for commit!"
    exit 0
else
    echo -e "${RED}❌ SOME LINTERS FAILED${NC}"
    echo ""
    echo "Please fix the issues above before committing."
    echo ""
    echo "Quick fixes:"
    echo "  ruff check --fix .     # Auto-fix ruff issues"
    echo "  black .                # Auto-format code"
    echo "  isort . --skip .venv   # Auto-sort imports"
    exit 1
fi
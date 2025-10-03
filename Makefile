.PHONY: help install install-dev test test-unit test-integration lint lint-fix type security coverage clean pre-commit setup-hooks run docker-build docker-up docker-down

# Default target
.DEFAULT_GOAL := help

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(BLUE)Dartserver Python App - Available Commands$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""

# Installation targets
install: ## Install production dependencies with UV
	@echo "$(BLUE)Installing production dependencies...$(NC)"
	uv pip install -e .

install-dev: ## Install development dependencies with UV
	@echo "$(BLUE)Installing development dependencies...$(NC)"
	uv pip install -e ".[dev,lint,test]"
	@echo "$(GREEN)✓ Development dependencies installed$(NC)"

install-all: ## Install all dependencies including optional ones
	@echo "$(BLUE)Installing all dependencies...$(NC)"
	uv pip install -e ".[all]"
	@echo "$(GREEN)✓ All dependencies installed$(NC)"

# Testing targets
test: ## Run all tests with pytest
	@echo "$(BLUE)Running all tests...$(NC)"
	pytest tests/ -v

test-unit: ## Run unit tests only
	@echo "$(BLUE)Running unit tests...$(NC)"
	pytest tests/unit/ -v -m unit

test-integration: ## Run integration tests only
	@echo "$(BLUE)Running integration tests...$(NC)"
	pytest tests/integration/ -v -m integration

test-cov: ## Run tests with coverage report
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	pytest tests/ --cov=. --cov-report=term-missing --cov-report=html:build/coverage/html --cov-report=xml:build/coverage/coverage.xml --cov-report=json:build/coverage/coverage.json --junit-xml=build/reports/junit.xml

test-watch: ## Run tests in watch mode
	@echo "$(BLUE)Running tests in watch mode...$(NC)"
	pytest-watch tests/

# Linting targets
lint: ## Run all linting checks
	@echo "$(BLUE)Running linting checks...$(NC)"
	@echo "$(YELLOW)→ Ruff$(NC)"
	ruff check .
	@echo "$(YELLOW)→ Black$(NC)"
	black --check --diff .
	@echo "$(YELLOW)→ isort$(NC)"
	isort --check-only --diff .
	@echo "$(YELLOW)→ Flake8$(NC)"
	flake8 .
	@echo "$(GREEN)✓ All linting checks passed$(NC)"

lint-fix: ## Run linting checks and auto-fix issues
	@echo "$(BLUE)Running linting with auto-fix...$(NC)"
	@echo "$(YELLOW)→ Ruff (fixing)$(NC)"
	ruff check --fix .
	@echo "$(YELLOW)→ Black (formatting)$(NC)"
	black .
	@echo "$(YELLOW)→ isort (sorting imports)$(NC)"
	isort .
	@echo "$(GREEN)✓ All fixes applied$(NC)"

type: ## Run type checking with mypy
	@echo "$(BLUE)Running type checking...$(NC)"
	mypy .

security: ## Run security checks
	@echo "$(BLUE)Running security checks...$(NC)"
	@echo "$(YELLOW)→ Bandit$(NC)"
	bandit -r . -c pyproject.toml
	@echo "$(YELLOW)→ Safety$(NC)"
	safety check --json || true
	@echo "$(GREEN)✓ Security checks complete$(NC)"

pylint: ## Run pylint checks
	@echo "$(BLUE)Running pylint...$(NC)"
	pylint app.py game_manager.py rabbitmq_consumer.py games/

# Coverage targets
coverage: ## Generate coverage report
	@echo "$(BLUE)Generating coverage report...$(NC)"
	coverage run -m pytest tests/
	coverage report
	coverage html -d build/coverage/html
	coverage xml -o build/coverage/coverage.xml
	coverage json -o build/coverage/coverage.json
	@echo "$(GREEN)✓ Coverage report generated in build/coverage/$(NC)"

coverage-report: ## Show coverage report
	@echo "$(BLUE)Coverage Report:$(NC)"
	coverage report

# Documentation targets
docs: ## Build documentation
	@echo "$(BLUE)Building documentation...$(NC)"
	tox -e docs
	@echo "$(GREEN)✓ Documentation built in docs/build/html/$(NC)"

# Tox targets
tox: ## Run tox for all environments
	@echo "$(BLUE)Running tox...$(NC)"
	tox

tox-lint: ## Run tox linting environment
	@echo "$(BLUE)Running tox lint environment...$(NC)"
	tox -e lint

tox-type: ## Run tox type checking environment
	@echo "$(BLUE)Running tox type environment...$(NC)"
	tox -e type

tox-security: ## Run tox security environment
	@echo "$(BLUE)Running tox security environment...$(NC)"
	tox -e security

tox-py310: ## Run tox for Python 3.10
	@echo "$(BLUE)Running tox for Python 3.10...$(NC)"
	tox -e py310

tox-py311: ## Run tox for Python 3.11
	@echo "$(BLUE)Running tox for Python 3.11...$(NC)"
	tox -e py311

tox-py312: ## Run tox for Python 3.12
	@echo "$(BLUE)Running tox for Python 3.12...$(NC)"
	tox -e py312

# Pre-commit targets
pre-commit: ## Run pre-commit hooks on all files
	@echo "$(BLUE)Running pre-commit hooks...$(NC)"
	pre-commit run --all-files

pre-commit-install: ## Install pre-commit hooks
	@echo "$(BLUE)Installing pre-commit hooks...$(NC)"
	pre-commit install
	@echo "$(GREEN)✓ Pre-commit hooks installed$(NC)"

setup-hooks: ## Setup custom git hooks
	@echo "$(BLUE)Setting up custom git hooks...$(NC)"
	chmod +x .git-hooks/pre-commit
	cp .git-hooks/pre-commit .git/hooks/pre-commit
	@echo "$(GREEN)✓ Custom git hooks installed$(NC)"

# Cleanup targets
clean: ## Clean up build artifacts and cache
	@echo "$(BLUE)Cleaning up...$(NC)"
	find build/coverage -mindepth 1 ! -name '.gitkeep' -delete 2>/dev/null || true
	find build/reports -mindepth 1 ! -name '.gitkeep' -delete 2>/dev/null || true
	rm -rf build/lib/
	rm -rf build/bdist.*/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	rm -rf .tox/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	@echo "$(GREEN)✓ Cleanup complete$(NC)"

clean-all: clean ## Clean everything including virtual environments
	@echo "$(BLUE)Deep cleaning...$(NC)"
	rm -rf .venv/
	rm -rf venv/
	@echo "$(GREEN)✓ Deep cleanup complete$(NC)"

# Application targets
run: ## Run the application
	@echo "$(BLUE)Starting Dartserver application...$(NC)"
	python app.py

run-dev: ## Run the application in development mode
	@echo "$(BLUE)Starting Dartserver in development mode...$(NC)"
	FLASK_DEBUG=True python app.py

# Docker targets
docker-build: ## Build Docker image
	@echo "$(BLUE)Building Docker image...$(NC)"
	docker-compose build

docker-up: ## Start Docker containers
	@echo "$(BLUE)Starting Docker containers...$(NC)"
	docker-compose up -d

docker-down: ## Stop Docker containers
	@echo "$(BLUE)Stopping Docker containers...$(NC)"
	docker-compose down

docker-logs: ## Show Docker logs
	@echo "$(BLUE)Docker logs:$(NC)"
	docker-compose logs -f

docker-restart: docker-down docker-up ## Restart Docker containers

# Quality checks (all)
check-all: lint type security test ## Run all quality checks

# CI/CD simulation
ci: clean install-dev lint type security test coverage ## Simulate CI pipeline

# Development setup
dev-setup: install-dev pre-commit-install setup-hooks ## Complete development setup
	@echo ""
	@echo "$(GREEN)========================================$(NC)"
	@echo "$(GREEN)  Development Environment Ready! 🚀$(NC)"
	@echo "$(GREEN)========================================$(NC)"
	@echo ""
	@echo "Next steps:"
	@echo "  1. Run '$(YELLOW)make test$(NC)' to run tests"
	@echo "  2. Run '$(YELLOW)make lint$(NC)' to check code quality"
	@echo "  3. Run '$(YELLOW)make run$(NC)' to start the application"
	@echo ""

# Show project info
info: ## Show project information
	@echo "$(BLUE)Project Information:$(NC)"
	@echo "  Name: dartserver-pythonapp"
	@echo "  Python: $$(python --version)"
	@echo "  UV: $$(uv --version 2>/dev/null || echo 'Not installed')"
	@echo "  Pytest: $$(pytest --version 2>/dev/null || echo 'Not installed')"
	@echo "  Tox: $$(tox --version 2>/dev/null || echo 'Not installed')"
	@echo ""
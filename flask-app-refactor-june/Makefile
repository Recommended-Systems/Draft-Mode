# Makefile for Draft Mode development and testing

.PHONY: help install install-dev test test-unit test-integration coverage lint format security clean run-dev run-prod migrate

help:  ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Installation
install:  ## Install production dependencies
	pip install -r requirements.txt

install-dev:  ## Install development and testing dependencies
	pip install -r requirements.txt
	pip install -r requirements-test.txt

# Testing
test:  ## Run all tests with coverage
	pytest --cov=. --cov-report=html --cov-report=term-missing

test-unit:  ## Run unit tests only
	pytest tests/unit/ -v

test-integration:  ## Run integration tests only
	pytest tests/integration/ -v

test-fast:  ## Run tests in parallel (faster)
	pytest -n auto

test-verbose:  ## Run tests with verbose output
	pytest -vv -s

coverage:  ## Generate and open coverage report
	pytest --cov=. --cov-report=html
	@echo "Opening coverage report..."
	@python -m webbrowser htmlcov/index.html || open htmlcov/index.html

# Code Quality
lint:  ## Run code linters
	@echo "Running flake8..."
	flake8 . --exclude=venv,migrations --max-line-length=120
	@echo "Running mypy..."
	mypy . --exclude=venv --exclude=migrations --ignore-missing-imports

format:  ## Format code with black and isort
	@echo "Formatting with black..."
	black . --exclude=venv
	@echo "Sorting imports with isort..."
	isort . --skip venv --skip migrations

format-check:  ## Check if code needs formatting
	black . --check --exclude=venv
	isort . --check --skip venv --skip migrations

# Security
security:  ## Run security checks
	@echo "Checking for known vulnerabilities..."
	safety check
	@echo "Running security linter..."
	bandit -r . -x ./tests,./venv,./migrations

security-audit:  ## Full security audit
	@echo "Running comprehensive security audit..."
	safety check --json
	bandit -r . -f json -o bandit-report.json -x ./tests,./venv,./migrations
	@echo "Security reports generated: bandit-report.json"

# Database
migrate:  ## Run database migrations
	flask db upgrade

migrate-create:  ## Create a new migration
	@read -p "Enter migration message: " msg; \
	flask db migrate -m "$$msg"

migrate-rollback:  ## Rollback last migration
	flask db downgrade

# Development
run-dev:  ## Run development server
	python app.py

run-prod:  ## Run production server with gunicorn
	gunicorn -w 4 -b 0.0.0.0:8000 "app:create_app('production')"

# Cleanup
clean:  ## Remove temporary files
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name ".coverage" -delete
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf dist/
	rm -rf build/

clean-db:  ## Remove database files
	rm -f *.db

# CI/CD
ci:  ## Run all CI checks (tests, linting, security)
	@echo "Running CI checks..."
	make format-check
	make lint
	make security
	make test
	@echo "✅ All CI checks passed!"

pre-commit:  ## Run pre-commit checks
	make format
	make lint
	make test-fast

# Docker (if needed in future)
docker-build:  ## Build Docker image
	docker build -t draft-mode:latest .

docker-run:  ## Run Docker container
	docker run -p 5000:5000 draft-mode:latest

# Documentation
docs:  ## Generate documentation
	@echo "Documentation is in docs/ directory"
	@echo "Tests documentation: tests/README.md"

# Quick commands for development workflow
quick-test:  ## Quick test (fast, no coverage)
	pytest tests/ -x -v

watch-test:  ## Watch files and re-run tests on change
	pytest-watch

init-db:  ## Initialize database with migrations
	flask db init
	flask db migrate -m "Initial migration"
	flask db upgrade

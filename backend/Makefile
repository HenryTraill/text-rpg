.PHONY: help install install-dev test test-cov test-unit test-middleware test-integration clean lint format run run-dev db-upgrade db-downgrade db-revision docker-build docker-up docker-down

# Default target
help:
	@echo "=== Text RPG Backend - Available Commands ==="
	@echo ""
	@echo "Environment Setup:"
	@echo "  install       Install production dependencies"
	@echo "  install-dev   Install all dependencies (including dev/test)"
	@echo "  venv          Create virtual environment"
	@echo ""
	@echo "Development:"
	@echo "  run           Run the development server"
	@echo "  run-dev       Run the development server with hot reload"
	@echo "  run-prod      Run the production server"
	@echo ""
	@echo "Testing:"
	@echo "  test          Run all tests"
	@echo "  test-cov      Run tests with coverage report"
	@echo "  test-unit     Run unit tests only"
	@echo "  test-middleware  Run middleware tests only"
	@echo "  test-integration Run integration tests only"
	@echo "  test-watch    Run tests in watch mode"
	@echo "  test-auth     Run authentication tests only"
	@echo "  test-health   Run health check tests only"
	@echo ""
	@echo "Code Quality:"
	@echo "  lint          Run linting checks"
	@echo "  lint-fix      Run linting with auto-fix"
	@echo "  format        Format code with black and isort"
	@echo "  format-check  Check code formatting without making changes"
	@echo "  type-check    Run type checking with mypy"
	@echo ""
	@echo "Database:"
	@echo "  db-upgrade    Run database migrations"
	@echo "  db-downgrade  Rollback last database migration"
	@echo "  db-revision   Create new database migration"
	@echo "  db-reset      Reset database (drop and recreate)"
	@echo "  db-current    Show current migration version"
	@echo "  db-history    Show migration history"
	@echo ""
	@echo "Docker:"
	@echo "  docker-build  Build Docker images"
	@echo "  docker-up     Start services with Docker Compose"
	@echo "  docker-down   Stop Docker Compose services"
	@echo "  docker-logs   Show Docker logs"
	@echo "  docker-shell  Get shell access to backend container"
	@echo "  docker-db     Access PostgreSQL shell in container"
	@echo "  docker-redis  Access Redis CLI in container"
	@echo ""
	@echo "Cleanup:"
	@echo "  clean         Remove temporary files and caches"
	@echo "  clean-pyc     Remove Python bytecode files"
	@echo "  clean-test    Remove test and coverage artifacts"
	@echo "  clean-docker  Remove Docker containers and images"

# Environment Setup
venv:
	python3 -m venv env
	@echo "Virtual environment created. Activate with: source env/bin/activate"

install:
	pip install --upgrade pip
	pip install -r requirements.txt

install-dev:
	pip install --upgrade pip
	pip install -r requirements.txt
	pip install -r requirements-test.txt

# Development Server
run:
	python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

run-dev:
	python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

run-prod:
	python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# Testing
test:
	python run_tests.py

test-cov:
	python run_tests.py --coverage

test-unit:
	python -m pytest tests/unit/ -v

test-middleware:
	python -m pytest tests/middleware/ -v

test-integration:
	python -m pytest tests/integration/ -v

test-auth:
	python -m pytest -m auth -v

test-health:
	python -m pytest -m health -v

test-watch:
	python -m pytest-watch

# Code Quality
lint:
	python -m flake8 app tests --max-line-length=88 --extend-ignore=E203,W503
	python -m mypy app --ignore-missing-imports

lint-fix:
	python -m autopep8 --in-place --recursive app tests

format:
	python -m black app tests
	python -m isort app tests --profile black

format-check:
	python -m black --check app tests
	python -m isort --check-only app tests --profile black

type-check:
	python -m mypy app --ignore-missing-imports

# Database Operations
db-upgrade:
	alembic upgrade head

db-downgrade:
	alembic downgrade -1

db-revision:
	@echo "Enter migration message:"
	@read -r msg && alembic revision --autogenerate -m "$$msg"

db-reset:
	alembic downgrade base
	alembic upgrade head

db-current:
	alembic current

db-history:
	alembic history

# Docker Operations (from project root)
docker-build:
	cd .. && docker-compose build

docker-up:
	cd .. && docker-compose up -d

docker-down:
	cd .. && docker-compose down

docker-logs:
	cd .. && docker-compose logs -f

docker-shell:
	cd .. && docker-compose exec backend bash

docker-db:
	cd .. && docker-compose exec postgres psql -U postgres -d text_rpg_db

docker-redis:
	cd .. && docker-compose exec redis redis-cli

docker-restart:
	cd .. && docker-compose restart

# Development with Docker
dev-up:
	cd .. && docker-compose up

dev-down:
	cd .. && docker-compose down

dev-rebuild:
	cd .. && docker-compose down
	cd .. && docker-compose build --no-cache
	cd .. && docker-compose up

# Cleanup
clean: clean-pyc clean-test
	find . -name '*.egg-info' -exec rm -rf {} +
	find . -name '*.egg' -exec rm -f {} +
	find . -name '.DS_Store' -exec rm -f {} +

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -rf {} +

clean-test:
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf coverage.xml
	rm -rf .pytest_cache/
	rm -rf test.db
	rm -rf test.db-journal

clean-docker:
	cd .. && docker-compose down -v
	docker system prune -f

# Development helpers
check: format-check lint type-check test

install-all: install-dev
	pip install pre-commit
	pre-commit install

setup: venv install-all
	@echo "Setup complete! Activate venv with: source env/bin/activate"

# Health checks
health:
	curl -f http://localhost:8000/health || echo "Backend not running"

ready:
	curl -f http://localhost:8000/ready || echo "Backend not ready"

alive:
	curl -f http://localhost:8000/alive || echo "Backend not alive" 
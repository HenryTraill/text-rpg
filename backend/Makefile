.PHONY: help install install-dev test test-cov clean lint format run run-dev db-upgrade db-downgrade db-revision docker-build docker-up docker-down

# Default target
help:
	@echo "Available commands:"
	@echo "  help          Show this help message"
	@echo ""
	@echo "Environment Setup:"
	@echo "  install       Install production dependencies"
	@echo "  install-dev   Install all dependencies (including dev/test)"
	@echo ""
	@echo "Development:"
	@echo "  run           Run the development server"
	@echo "  run-dev       Run the development server with hot reload"
	@echo "  test          Run tests"
	@echo "  test-cov      Run tests with coverage report"
	@echo "  test-watch    Run tests in watch mode"
	@echo ""
	@echo "Code Quality:"
	@echo "  lint          Run linting checks"
	@echo "  format        Format code with black and isort"
	@echo "  format-check  Check code formatting without making changes"
	@echo ""
	@echo "Database:"
	@echo "  db-upgrade    Run database migrations"
	@echo "  db-downgrade  Rollback last database migration"
	@echo "  db-revision   Create new database migration"
	@echo "  db-reset      Reset database (drop and recreate)"
	@echo ""
	@echo "Docker:"
	@echo "  docker-build  Build Docker images"
	@echo "  docker-up     Start services with Docker Compose"
	@echo "  docker-down   Stop Docker Compose services"
	@echo "  docker-logs   Show Docker logs"
	@echo ""
	@echo "Cleanup:"
	@echo "  clean         Remove temporary files and caches"
	@echo "  clean-pyc     Remove Python bytecode files"
	@echo "  clean-test    Remove test and coverage artifacts"

# Environment Setup
install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements.txt -r requirements-test.txt

# Development Server
run:
	python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

run-dev:
	python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Testing
test:
	python -m pytest

test-cov:
	python -m pytest --cov --cov-report=html:htmlcov --cov-report=term

test-watch:
	python -m pytest --watch

# Code Quality
lint:
	python -m flake8 app tests
	python -m mypy app

format:
	python -m black app tests
	python -m isort app tests

format-check:
	python -m black --check app tests
	python -m isort --check-only app tests

# Database Operations
db-upgrade:
	alembic upgrade head

db-downgrade:
	alembbic downgrade -1

db-revision:
	@read -p "Enter migration message: " msg; \
	alembic revision --autogenerate -m "$$msg"

db-reset:
	alembic downgrade base
	alembic upgrade head

# Docker Operations
docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

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
	rm -rf backend/htmlcov/
	rm -rf backend/.coverage
	rm -rf backend/.pytest_cache/
	rm -rf backend/test.db 
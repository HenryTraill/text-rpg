# Development Setup Guide

This guide will help you set up the development environment for the Text RPG project.

## Prerequisites

- Docker and Docker Compose
- Python 3.11+
- Git

## Quick Start with Docker

1. **Clone the repository**
   ```bash
   git clone https://github.com/HenryTraill/text-rpg.git
   cd text-rpg
   ```

2. **Copy environment configuration**
   ```bash
   cp backend/env.example backend/.env
   ```
   Edit `backend/.env` with your preferred settings.

3. **Start all services**
   ```bash
   docker-compose up -d
   ```

4. **Run database migrations**
   ```bash
   docker-compose run --rm migrations
   ```

5. **Access the application**
   - API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

## Development Workflow

### Running Services

```bash
# Start all services in background
docker-compose up -d

# Start only specific services
docker-compose up -d postgres redis

# View logs
docker-compose logs -f backend

# Stop all services
docker-compose down
```

### Database Management

```bash
# Run migrations
docker-compose run --rm migrations

# Create new migration
docker-compose run --rm backend alembic revision --autogenerate -m "description"

# Reset database (careful!)
docker-compose down -v
docker-compose up -d postgres
docker-compose run --rm migrations
```

### Testing

```bash
# Run tests in container
docker-compose run --rm backend pytest

# Run tests with coverage
docker-compose run --rm backend pytest --cov=app --cov-report=html

# Run specific test file
docker-compose run --rm backend pytest tests/test_models.py
```

## Local Development (without Docker)

If you prefer local development:

1. **Set up virtual environment**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-test.txt
   ```

3. **Start local services**
   ```bash
   # You'll need PostgreSQL and Redis running locally
   # Update backend/.env with local connection strings
   ```

4. **Run the application**
   ```bash
   uvicorn app.main:app --reload
   ```

## Code Quality Setup

### Pre-commit Hooks

1. **Install pre-commit**
   ```bash
   pip install pre-commit
   ```

2. **Install hooks**
   ```bash
   pre-commit install
   ```

3. **Run on all files (optional)**
   ```bash
   pre-commit run --all-files
   ```

### Code Formatting

The pre-commit hooks will automatically:
- Format Python code with Black
- Sort imports with isort
- Lint with flake8
- Type check with mypy
- Security scan with bandit
- Lint Dockerfiles with hadolint

## Environment Variables

Key environment variables (see `backend/env.example`):

| Variable | Description | Default |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection string | postgres://postgres:password@localhost:5432/text_rpg_db |
| `REDIS_URL` | Redis connection string | redis://localhost:6379 |
| `SECRET_KEY` | JWT secret key | your-secret-key-change-this-in-production |
| `DEBUG` | Enable debug mode | true |
| `ENVIRONMENT` | Environment (development/production) | development |

## Service Ports

| Service | Port | Description |
|---------|------|-------------|
| Backend API | 8000 | FastAPI application |
| PostgreSQL | 5432 | Database |
| Redis | 6379 | Cache and pub/sub |

## Troubleshooting

### Common Issues

1. **Port conflicts**
   ```bash
   # Check what's using the port
   lsof -i :8000
   # Kill the process or change ports in docker-compose.yml
   ```

2. **Database connection issues**
   ```bash
   # Check if PostgreSQL is running
   docker-compose ps postgres
   # Check logs
   docker-compose logs postgres
   ```

3. **Permission issues on Linux**
   ```bash
   # Fix file permissions
   sudo chown -R $USER:$USER .
   ```

### Reset Everything

```bash
# Stop and remove all containers, networks, and volumes
docker-compose down -v --remove-orphans

# Remove images (optional)
docker-compose down --rmi all

# Start fresh
docker-compose up -d
docker-compose run --rm migrations
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Set up pre-commit hooks
4. Make your changes
5. Run tests
6. Submit a pull request

The CI/CD pipeline will automatically run tests and code quality checks on all pull requests.

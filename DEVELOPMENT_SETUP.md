# Development Setup Guide

This guide will help you set up the local development environment for the Text RPG project.

## Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Git
- Node.js 18+ (for frontend development)

## Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/HenryTraill/text-rpg.git
   cd text-rpg
   ```

2. **Set up PostgreSQL Database**
   ```bash
   # Create database
   createdb text_rpg_db
   
   # Create user (optional)
   psql -c "CREATE USER text_rpg_user WITH PASSWORD 'your_password';"
   psql -c "GRANT ALL PRIVILEGES ON DATABASE text_rpg_db TO text_rpg_user;"
   ```

3. **Set up Redis**
   ```bash
   # Start Redis server
   redis-server
   ```

4. **Backend Setup**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

5. **Copy environment configuration**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` with your local database and Redis connection strings.

6. **Run database migrations**
   ```bash
   alembic upgrade head
   ```

7. **Start the backend server**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

8. **Frontend Setup (in new terminal)**
   ```bash
   cd frontend
   npm install
   npm start
   ```

9. **Access the application**
   - API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - Frontend: http://localhost:3000

## Development Workflow

### Running Services

```bash
# Start PostgreSQL (varies by OS)
# macOS with Homebrew:
brew services start postgresql

# Ubuntu/Debian:
sudo systemctl start postgresql

# Start Redis
redis-server

# Start backend (in backend directory)
source venv/bin/activate
uvicorn app.main:app --reload

# Start frontend (in frontend directory)
npm start
```

### Database Management

```bash
# Run migrations
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "description"

# Reset database (careful!)
dropdb text_rpg_db
createdb text_rpg_db
alembic upgrade head
```

### Testing

```bash
# Backend tests
cd backend
source venv/bin/activate
pytest

# Run tests with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_models.py

# Frontend tests
cd frontend
npm test
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

## Environment Variables

Key environment variables (see `backend/.env.example`):

| Variable | Description | Default |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection string | postgresql://localhost:5432/text_rpg_db |
| `REDIS_URL` | Redis connection string | redis://localhost:6379 |
| `SECRET_KEY` | JWT secret key | your-secret-key-change-this-in-production |
| `DEBUG` | Enable debug mode | true |
| `ENVIRONMENT` | Environment (development/production) | development |

## Service Ports

| Service | Port | Description |
|---------|------|-------------|
| Backend API | 8000 | FastAPI application |
| Frontend | 3000 | React development server |
| PostgreSQL | 5432 | Database |
| Redis | 6379 | Cache and pub/sub |

## Troubleshooting

### Common Issues

1. **Port conflicts**
   ```bash
   # Check what's using the port
   lsof -i :8000
   # Kill the process or change ports
   ```

2. **Database connection issues**
   ```bash
   # Check if PostgreSQL is running
   pg_isready -h localhost -p 5432
   # Check PostgreSQL status
   brew services list | grep postgresql  # macOS
   sudo systemctl status postgresql      # Linux
   ```

3. **Redis connection issues**
   ```bash
   # Check if Redis is running
   redis-cli ping
   # Should return PONG
   ```

4. **Virtual environment issues**
   ```bash
   # Recreate virtual environment
   rm -rf venv
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

### Reset Everything

```bash
# Stop all services
# Backend: Ctrl+C in terminal
# Frontend: Ctrl+C in terminal
# PostgreSQL: brew services stop postgresql (macOS)
# Redis: Ctrl+C if running in foreground

# Reset database
dropdb text_rpg_db
createdb text_rpg_db

# Restart services and run migrations
alembic upgrade head
```

## Installation by Operating System

### macOS Setup

```bash
# Install Homebrew if not installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install python@3.11 postgresql redis node

# Start services
brew services start postgresql
brew services start redis
```

### Ubuntu/Debian Setup

```bash
# Update package list
sudo apt update

# Install Python 3.11
sudo apt install python3.11 python3.11-venv python3.11-dev

# Install PostgreSQL
sudo apt install postgresql postgresql-contrib

# Install Redis
sudo apt install redis-server

# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install nodejs

# Start services
sudo systemctl start postgresql
sudo systemctl start redis-server
sudo systemctl enable postgresql
sudo systemctl enable redis-server
```

### Windows Setup

```bash
# Install Python 3.11 from python.org
# Install PostgreSQL from postgresql.org
# Install Redis from GitHub releases or use WSL
# Install Node.js from nodejs.org

# Set up PostgreSQL (in Command Prompt as Administrator)
createdb text_rpg_db

# Start Redis (if using Windows port)
redis-server
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Set up pre-commit hooks
4. Make your changes
5. Run tests locally
6. Submit a pull request

## Production Deployment

For production deployment:

1. Set up production PostgreSQL and Redis instances
2. Configure environment variables for production
3. Use a process manager like systemd or supervisor
4. Set up a reverse proxy (nginx)
5. Configure SSL certificates
6. Set up monitoring and logging

The application is designed to be easily deployable to cloud platforms or VPS instances without containerization.

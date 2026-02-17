# CONTRIBUTING

## Getting Started

### Prerequisites (Debian/Ubuntu)

This project requires Python 3.13+, Docker, and Node.js for markdown linting. Follow the steps below to set up your development environment on a Debian-based system.

#### 1. Install System Dependencies

```shell
# Update package manager
sudo apt update

# Install Python and virtual environment tools
sudo apt install -y python3.13 python3.13-venv python3.13-dev

# Install Docker (if not already installed)
sudo apt install -y docker.io docker-compose-v2

# Add your user to the docker group (avoid using sudo with docker)
sudo usermod -aG docker $USER
# Log out and back in, or run: newgrp docker

# Install Node.js and npm for markdown linting (optional but recommended)
sudo apt install -y nodejs npm
sudo npm install -g markdownlint-cli
```

#### 2. Clone the Repository

```shell
cd /path/to/projects
git clone https://github.com/yourusername/clicknback.git
cd clicknback
```

#### 3. Set Up Python Environment

The project uses a Makefile for common tasks. The `make install` command will create and activate a virtual environment and install all dependencies:

```shell
make install
```

This will:

- Create a `.venv` virtual environment
- Install production dependencies
- Install development dependencies (pytest, linting tools, etc.)

#### 4. Start the Database

This project uses PostgreSQL in Docker. Start it with:

```shell
make up
```

This will:

- Create a Docker network (`clicknback-nw`)
- Start PostgreSQL container with the database initialized
- Run pending migrations automatically

#### 5. Verify Your Setup

```shell
# Run the test suite
make test

# Start the development server (in another terminal)
# First, activate the venv again if needed
source .venv/bin/activate
make run
```

The API will be available at `http://localhost:8000` with interactive docs at `http://localhost:8000/docs`.

### Common Development Tasks

```shell
# Install dependencies and set up venv
make install     # Create .venv and install all dependencies

# Start/stop the application and database
make up          # Start containers and database
make down        # Stop containers and remove network

# Run tests
make test        # Run tests with coverage (pytest)

# Code quality
make lint        # Run all linters (markdown, flake8, isort, black)
make format      # Auto-format code (isort, black)

# Start development server
make run         # Start FastAPI server with auto-reload

# Reset database (useful during development)
make db-reset    # Rollback migrations, apply fresh migrations, seed data

# Clean up artifacts
make clean       # Remove .venv, __pycache__, coverage reports, etc.
```

## Architecture & Design Decisions

This project follows a modular monolith architecture with clear separation of concerns. Key architectural decisions are documented as Architecture Decision Records (ADRs) in the [`docs/adr/`](docs/adr/) directory.

**We recommend reviewing relevant ADRs before proposing architectural changes.** They provide important context and rationale behind design choices.

Follow a pragmatic approach:

- For architectural decisions not yet documented in ADRs, favor solutions that are **practical** for current needs while leaving room for future scalability
- Prioritize **simplicity and maintainability** over over-engineering
- Keep options open for growth as the project evolves

## Quality Enforcement

To ensure code quality and consistency, always run the following before pushing or opening a pull request:

```shell
make lint   # Check code style, formatting, and docs
make test   # Run all tests with coverage
```

Refer to the Architecture Decision Records (ADRs) in `docs/adr/` for details on the project's testing and quality strategy.

## Database Migrations

This project uses Alembic for database schema migrations.

### Creating Migrations

1. Make changes to models in `app/<domain>>/models.py`
2. Generate migration:

```shell
source .venv/bin/activate
alembic revision --autogenerate -m "Add new field"
```

<!-- markdownlint-disable MD029 -->
3. Review the generated migration in `alembic/versions/`
4. Apply the migration:

    ```shell
    alembic upgrade head
    ```
<!-- markdownlint-enable MD029 -->

### Working with Migrations

```shell
# View migration history
alembic history

# Upgrade to latest
alembic upgrade head

# Downgrade one step
alembic downgrade -1

# Downgrade to base
alembic downgrade base
```

## Troubleshooting

### Virtual Environment Issues

```shell
# If you see "command not found: python3.13"
python3 --version  # Check your Python version
# Create venv with your available version:
python3 -m venv .venv

# If venv is broken
make clean 
make install
```

### Docker Issues

```shell
# If containers won't start
docker system prune  # Remove unused images/volumes

# If you can't connect to Docker
# Make sure you've added your user to the docker group:
sudo usermod -aG docker $USER
newgrp docker

# Check if Docker is running
sudo systemctl status docker
```

### Database Connection Issues

```shell
# Check if PostgreSQL is running
docker ps | grep clicknback

# View logs
docker logs clicknback-clicknback-db-1

# Reset the database
make db-reset
```

### Port Already in Use

If port 8000 (FastAPI) or 5432 (PostgreSQL) is already in use:

```shell
# Find what's using the port
sudo lsof -i :8000

# Kill the process (if needed)
kill -9 <PID>

# Or use a different port for FastAPI
source .venv/bin/activate
uvicorn app.main:app --reload --port 8001
```

## Questions or Issues?

- Check the documentation in [`docs/`](docs/)
- Review relevant ADRs in [`docs/adr/`](docs/adr/)
- Check existing GitHub issues
- Open an issue with details about the problem and your environment

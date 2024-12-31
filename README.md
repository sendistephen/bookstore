# Bookstore API

A robust Flask-based backend application for managing a bookstore, featuring comprehensive book management, customer interactions, and administrative capabilities.

## Overview

This API powers a modern bookstore platform with features including inventory management, customer accounts, order processing, and secure payments. Built with scalability and maintainability in mind using Python, Flask, PostgreSQL, and Docker.

## Technology Stack

- **Backend Framework**: Python 3.9, Flask
- **Database**: PostgreSQL
- **Caching**: Redis
- **Containerization**: Docker, Docker Compose
- **Web Server**: Nginx
- **Migration Tool**: Alembic
- **Task Queue**: Celery (coming soon)

## Project Structure

```
bookstore/
├── app/                    # Application code
│   ├── api/               # API endpoints and routes
│   ├── models/            # Database models
│   ├── schemas/           # Pydantic/Marshmallow schemas
│   ├── services/          # Business logic services
│   ├── templates/         # HTML templates
│   ├── extensions.py      # Flask extensions
│   └── __init__.py        # App factory and configuration
├── config/                # Configuration files
│   ├── config.py         # App configuration classes
│   └── logging_config.py  # Logging configuration
├── docker/                # Docker configuration
│   └── local/            # Local development setup
├── migrations/            # Database migrations
├── scripts/              # Utility scripts
├── tests/                # Test suite
├── utils/                # Helper utilities
├── .env                  # Environment variables
├── .env.example          # Example environment file
├── alembic.ini           # Alembic configuration
├── local.yml             # Docker Compose configuration
├── manage.py             # Management commands
├── requirements.txt      # Python dependencies
└── run.py               # Application entry point
```

## Features

### Book Management
- Create, read, update, and delete books
- Search by title, author, or genre
- Manage inventory and pricing

### Customer Features
- User registration and authentication
- Book browsing and searching
- Shopping cart management
- Order history

### Administrative Tools
- User management
- Order processing
- Inventory control
- Sales reporting

### Security
- Role-based access control
- Secure authentication
- Protected admin routes
- Data validation

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Make
- Git

### Quick Start

1. **Clone the Repository**
```bash
git clone https://github.com/sendi-stev/bookstore-api.git
cd bookstore-api
```

2. **Environment Setup**
```bash
# Copy environment files
cp .env.example .env
cp .admin_credentials.example .admin_credentials
```

3. **Launch Application**
```bash
# Build and start services
make build
make up

# Initialize database
make migrate
make seed-db
```

## Development Guide

### Development Workflow Commands

#### Docker Management
- `make build`: Build Docker images
- `make up`: Start services in detached mode
- `make down`: Stop services
- `make down-v`: Stop services and remove volumes
- `make reset-db`: Completely reset database (remove volumes, recreate, migrate, seed)
- `make clean`: Clean up Docker resources

#### Database Management
- `make migrate`: Run all pending database migrations
- `make migration MESSAGE="Your migration description"`: Create a new database migration
- `make seed-db`: Seed database with initial data
- `make create-admin`: Create an admin user

#### Development
- `make runserver`: Start development server
- `make test`: Run test suite

### Database Migrations

The project uses Alembic for database migrations. To create and apply migrations:

1. Create a new migration:
```bash
make migration MESSAGE="Description of schema changes"
```

2. Apply migrations:
```bash
make migrate
```

3. Reset database (drops and recreates):
```bash
make reset-db
```

### Troubleshooting

- If you encounter migration issues, use `make reset-db` to completely reset the database
- Check Docker logs with `docker-compose -f local.yml logs api` for detailed error messages
- Ensure all environment variables are correctly set in `.env`

## Testing

### Setup for Testing

1. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### Running Tests

Run the full test suite with coverage:
```bash
# Run all tests with verbose output and coverage
pytest -vv --cov=app

# Run tests for a specific module
pytest tests/unit/test_book_category_service.py

# Generate HTML coverage report
pytest --cov=app --cov-report=html
```

### Test Configuration

- Tests use an in-memory SQLite database
- Configuration is managed through `config/config.py`
- Test fixtures are defined in `tests/conftest.py`

### Common Test Commands

```bash
# Run tests and stop on first failure
pytest -x

# Run tests with detailed output
pytest -s

# Run tests matching a specific pattern
pytest -k "test_create"
```

### Code Quality Checks

```bash
# Run linters
flake8 app/
black --check app/
isort --check-only app/

# Run type checking
mypy app/
```

### Debugging Tests

If you encounter import or configuration issues:
1. Ensure all dependencies are installed
2. Check your Python path
3. Verify environment variables
4. Use `pytest -vv` for detailed output

## Deployment

### Fresh Installation

```bash
make build
make up
make migrate
make seed-db
```

### Update Existing Installation

```bash
git pull
make build
make migrate
make up
```

## Configuration

### Environment Variables

Key configuration variables in `.env`:

- `FLASK_ENV`: Application environment (development/production)
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `SECRET_KEY`: Application secret key

### Admin Setup

The `.admin_credentials` file is required for database seeding and contains initial admin user details. This file should be kept secure and not committed to version control.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contact

Sendi Steve - sendi.stev@gmail.com

Project Link: [https://github.com/sendi-stev/bookstore-api](https://github.com/sendi-stev/bookstore-api)
.PHONY: build up down down-v reset-db create-admin seed-db migrate migration runserver test clean help

# Build Docker images
build:
	@echo "Building Docker images..."
	docker compose -f local.yml build

# Start services in detached mode
up:
	@echo "Starting services..."
	docker compose -f local.yml up -d

# Stop services
down:
	@echo "Stopping services..."
	docker compose -f local.yml stop

# Stop and remove volumes
down-v:
	@echo "Stopping services and removing volumes..."
	docker compose -f local.yml down -v

# Reset database (remove volumes, recreate, and seed)
reset-db: down-v
	@echo "Resetting database..."
	docker compose -f local.yml up -d
	@echo "Waiting for database to be available..."
	sleep 5
	@echo "Creating database tables..."
	docker compose -f local.yml run --rm api python run.py create_db
	@echo "Waiting for database tables to be created..."
	sleep 5
	@echo "Running database migrations..."
	docker compose -f local.yml run --rm api alembic upgrade head
	@echo "Waiting for database migrations to complete..."
	sleep 5
	@echo "Seeding database with initial data..."
	docker compose -f local.yml run --rm api python run.py seed_db
	@echo "Waiting for database seeding to complete..."
	sleep 5
	@echo "Creating admin user..."
	docker compose -f local.yml run --rm api python manage.py create_admin
	@echo "Database reset and seeded successfully."

# Create initial migrations
migrate:
	@echo "Running database migrations..."
	docker compose -f local.yml run --rm api alembic upgrade head

# Create a new database migration
migration:
	@echo "Creating new database migration..."
	docker compose -f local.yml run --rm api alembic revision --autogenerate -m "$(MESSAGE)"

# Seed database with initial data
seed-db:
	@echo "Seeding database with initial data..."
	docker compose -f local.yml run --rm api python run.py seed_db

# Create admin user from .admin_credentials
create-admin:
	@echo "Creating admin user..."
	docker compose -f local.yml run --rm api python manage.py create_admin

# Run development server
runserver:
	@echo "Starting development server..."
	docker compose -f local.yml run --rm --service-ports api python run.py runserver

# Run tests
test:
	@echo "Running tests..."
	docker compose -f local.yml run --rm api pytest

# Clean up Docker resources
clean:
	@echo "Cleaning up Docker resources..."
	docker system prune -f
	docker volume prune -f

# Help target
help:
	@echo "Available targets:"
	@echo "  build       - Build Docker images"
	@echo "  up          - Start services"
	@echo "  down        - Stop services"
	@echo "  down-v      - Stop services and remove volumes"
	@echo "  reset-db    - Reset database (remove, recreate, seed)"
	@echo "  migrate     - Run database migrations"
	@echo "  migration   - Create a new database migration"
	@echo "  seed-db     - Seed database with initial data"
	@echo "  create-admin- Create admin user from .admin_credentials"
	@echo "  runserver   - Start development server"
	@echo "  test        - Run tests"
	@echo "  clean       - Clean up Docker resources"
	@echo "  help        - Show this help message"
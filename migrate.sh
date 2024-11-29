#!/bin/bash

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL to be ready..."
while ! docker compose -f local.yml exec postgres_db pg_isready -h localhost -p 5432 -U postgres; do
  echo "PostgreSQL is unavailable - sleeping"
  sleep 1
done

# Drop existing tables
echo "Dropping existing tables..."
docker compose -f local.yml exec postgres_db psql -U postgres -d bookstore -c "DROP TABLE IF EXISTS user_roles, users, roles, alembic_version CASCADE;"

# Run migrations
echo "Running migrations..."
docker compose -f local.yml run --rm api flask db upgrade

echo "Migration completed successfully!"

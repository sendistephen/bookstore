#!/bin/bash
# Migrate database script for production deployment

# Exit on any error
set -e

# Set environment variables
export FLASK_APP=app
export FLASK_ENV=production

# Run database migrations
flask db upgrade

# Optional: Add any additional setup or seeding
# flask db seed

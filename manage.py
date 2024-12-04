#!/usr/bin/env python3
import os
import sys
import click
import logging
from logging.config import dictConfig

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Configure logging
dictConfig({
    'version': 1,
    'formatters': {
        'default': {
            'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'default',
            'stream': 'ext://sys.stdout'
        }
    },
    'root': {
        'level': 'INFO',
        'handlers': ['console']
    }
})

logger = logging.getLogger(__name__)

from app import create_app
from app.extensions import db
from alembic import command
from alembic.config import Config
from scripts.seed_db import seed_roles

def get_alembic_config():
    """Get Alembic configuration"""
    cfg = Config("alembic.ini")
    cfg.set_main_option("script_location", "migrations")
    if os.getenv('DATABASE_URL'):
        cfg.set_main_option("sqlalchemy.url", os.getenv('DATABASE_URL'))
    return cfg

@click.group(name='manage')
def cli():
    """Database and migration management commands"""
    pass

@cli.command(name='init_migrations')
def init_migrations():
    """Initialize migrations"""
    try:
        logger.info("Initializing migrations...")
        # Check if migrations directory exists
        if not os.path.exists('migrations'):
            command.init(Config(), 'migrations')
            logger.info("Migrations directory created successfully!")
        
        # Create initial migration
        app = create_app()
        with app.app_context():
            alembic_cfg = get_alembic_config()
            command.revision(alembic_cfg, autogenerate=True, message='Initial migration')
            command.stamp(alembic_cfg, "head")
            logger.info("Initial migration created and database stamped!")
            
    except Exception as e:
        logger.error(f"Error initializing migrations: {e}")
        sys.exit(1)

@cli.command(name='make_migrations')
@click.option('-m', '--message', default='Update', help='Migration message')
def make_migrations(message):
    """Generate a new migration"""
    try:
        app = create_app()
        with app.app_context():
            alembic_cfg = get_alembic_config()
            command.revision(alembic_cfg, autogenerate=True, message=message)
        logger.info(f"Migration '{message}' created successfully!")
    except Exception as e:
        logger.error(f"Error creating migration: {e}")
        sys.exit(1)

@cli.command(name='migrate')
def migrate():
    """Apply all pending migrations"""
    try:
        app = create_app()
        with app.app_context():
            alembic_cfg = get_alembic_config()
            command.upgrade(alembic_cfg, "head")
        logger.info("Migrations applied successfully!")
    except Exception as e:
        logger.error(f"Error applying migrations: {e}")
        sys.exit(1)

@cli.command(name='rollback')
@click.option('--steps', default=1, help='Number of migrations to rollback')
def rollback(steps):
    """Rollback migrations"""
    try:
        app = create_app()
        with app.app_context():
            alembic_cfg = get_alembic_config()
            command.downgrade(alembic_cfg, f"-{steps}")
        logger.info(f"Rolled back {steps} migration(s) successfully!")
    except Exception as e:
        logger.error(f"Error rolling back migrations: {e}")
        sys.exit(1)

@cli.command(name='migration_status')
def migration_status():
    """Show current migration status"""
    try:
        app = create_app()
        with app.app_context():
            alembic_cfg = get_alembic_config()
            command.current(alembic_cfg)
        logger.info("Migration status displayed successfully!")
    except Exception as e:
        logger.error(f"Error displaying migration status: {e}")
        sys.exit(1)

@cli.command(name='seed_db')
def seed_db():
    """Seed the database with initial data"""
    try:
        app = create_app()
        with app.app_context():
            # Seed roles
            seed_roles()
            logger.info("Database seeded successfully!")
    except Exception as e:
        logger.error(f"Error seeding database: {e}")
        sys.exit(1)

@cli.command(name='create_admin')
@click.option('--email', help='Admin email')
@click.option('--username', help='Admin username')
@click.option('--password', help='Admin password')
def create_admin(email, username, password):
    """Create an admin user"""
    try:
        from scripts.seed_admin import create_admin_user
        
        success = create_admin_user(
            email=email,
            username=username,
            password=password
        )
        
        if success:
            logger.info(f"Admin user '{username or 'default'}' created successfully!")
        else:
            logger.warning("Failed to create admin user. Check logs for details.")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Error creating admin user: {e}")
        sys.exit(1)

if __name__ == '__main__':
    cli()

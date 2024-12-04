#!/usr/bin/env python3
import os
import sys
import argparse
import logging
from logging.config import dictConfig

# Configure logging
dictConfig({
    'version': 1,
    'formatters': {
        'default': {
            'format': '[%(asctime)s] %(levelname)s: %(message)s',
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

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app
from app.extensions import db
from scripts.seed_db import seed_roles
from scripts.seed_admin import create_admin_user

def create_db():
    """Create database tables"""
    try:
        app = create_app()
        with app.app_context():
            db.create_all()
            logger.info("Database tables created successfully!")
    except Exception as e:
        logger.error(f"Error creating database tables: {str(e)}")
        sys.exit(1)

def seed_db():
    """Seed the database with initial data"""
    try:
        app = create_app()
        with app.app_context():
            # Seed roles first
            seed_roles()
            
            # Check if an admin user exists, if not create one
            from app.models.user import User
            from app.models.role import Role
            
            admin_role = Role.query.filter_by(name='admin').first()
            admin_user = User.query.join(User.roles).filter(Role.name == 'admin').first()
            
            if not admin_user:
                # Generate a secure random admin user if none exists
                import secrets
                admin_email = f"admin_{secrets.token_hex(4)}@bookstore.local"
                admin_username = f"admin_{secrets.token_hex(4)}"
                admin_password = secrets.token_urlsafe(16)
                
                create_admin_user(
                    email=admin_email,
                    username=admin_username,
                    name="System Admin",
                    password=admin_password
                )
                
                logger.info("Generated default admin user:")
                logger.info(f"Email: {admin_email}")
                logger.info(f"Username: {admin_username}")
                logger.info("Please change the password immediately!")
            
            logger.info("Database seeded successfully!")
    except Exception as e:
        logger.error(f"Error seeding database: {str(e)}")
        sys.exit(1)

def runserver(host=None, port=None, debug=None):
    """Run the Flask development server"""
    try:
        app = create_app()
        
        # Use environment variables or default values
        host = host or os.getenv('API_HOST', '0.0.0.0')
        port = port or int(os.getenv('API_PORT', 5000))
        debug = debug if debug is not None else (os.getenv('FLASK_DEBUG', 'True').lower() == 'true')
        
        logger.info(f"Starting server on {host}:{port}")
        logger.info(f"Debug mode: {'enabled' if debug else 'disabled'}")
        
        app.run(host=host, port=port, debug=debug)
    except Exception as e:
        logger.error(f"Error starting server: {str(e)}")
        sys.exit(1)

def main():
    """Main entry point for CLI commands"""
    parser = argparse.ArgumentParser(description='Bookstore API management commands')
    parser.add_argument('command', choices=['create_db', 'seed_db', 'runserver'], 
                      help='Command to execute')
    parser.add_argument('--host', 
                      help='Host to run the server on (overrides environment)')
    parser.add_argument('--port', type=int, 
                      help='Port to run the server on (overrides environment)')
    parser.add_argument('--debug', action='store_true', 
                      help='Force debug mode (overrides environment)')

    args = parser.parse_args()

    try:
        if args.command == 'create_db':
            create_db()
        elif args.command == 'seed_db':
            seed_db()
        elif args.command == 'runserver':
            runserver(
                host=args.host, 
                port=args.port, 
                debug=args.debug
            )
        else:
            logger.error(f"Unknown command: {args.command}")
            parser.print_help()
            sys.exit(1)
    except Exception as e:
        logger.error(f"Execution error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
import os
import sys
import click
import logging

# Add the project root directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.role import Role

def read_credentials_from_file(file_path):
    """Read admin credentials from a file"""
    credentials = {}
    try:
        with open(file_path, 'r') as f:
            for line in f:
                key, value = line.strip().split('=', 1)
                credentials[key.lower()] = value
        return credentials
    except Exception as e:
        logging.error(f"Error reading credentials file: {e}")
        return None

def create_admin_user(email=None, username=None, name=None, password=None):
    """Create admin user with comprehensive validation"""
    # Try to read credentials from environment or file if not provided
    if not all([email, username, password]):
        # First, try environment variables
        email = email or os.getenv('ADMIN_EMAIL')
        username = username or os.getenv('ADMIN_USERNAME')
        password = password or os.getenv('ADMIN_PASSWORD')
        
        # If not in env, try reading from .admin_credentials file
        if not all([email, username, password]):
            credentials_file = os.path.join(project_root, '.admin_credentials')
            file_creds = read_credentials_from_file(credentials_file)
            if file_creds:
                email = email or file_creds.get('email')
                username = username or file_creds.get('username')
                password = password or file_creds.get('password')

    # Validate inputs
    if not all([email, username, password]):
        logging.error("Unable to retrieve admin credentials. Please provide email, username, and password.")
        return False

    name = name or "System Admin"

    app = create_app()

    with app.app_context():
        # Ensure database is created
        db.create_all()

        # Check if user already exists
        existing_user = User.query.filter(
            (User.email.ilike(email)) | (User.username.ilike(username))
        ).first()

        if existing_user:
            logging.info("Admin user already exists.")
            return False

        # Ensure admin role exists
        admin_role = Role.query.filter_by(name='admin').first()
        if not admin_role:
            admin_role = Role(name='admin')
            db.session.add(admin_role)

        # Create new admin user
        new_admin = User(
            email=email, 
            username=username,
            name=name, 
            is_verified=True, 
            is_active=True
        )

        # Set password
        new_admin.set_password(password)

        # Add roles
        new_admin.roles.append(admin_role)

        # Add to session and commit
        db.session.add(new_admin)
        try:
            db.session.commit()
            logging.info(f"Admin user '{username}' created successfully!")
            return True
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error creating admin user: {str(e)}")
            return False

@click.command()
@click.option('--email', help='Admin email')
@click.option('--username', help='Admin username')
@click.option('--name', default='System Admin', help='Admin name')
@click.option('--password', help='Admin password')
def cli(email, username, name, password):
    """Create an admin user"""
    success = create_admin_user(email, username, name, password)
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    cli()
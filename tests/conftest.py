import os
import sys

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

import pytest

# Optional imports
try:
    from flask_jwt_extended import create_access_token
except ImportError:
    create_access_token = None

try:
    from flask_session import Session
except ImportError:
    Session = None

from app import create_app
from app.extensions import db
from config.config import TestingConfig

@pytest.fixture(scope='session')
def app():
    """Create a Flask app configured for testing"""
    # Override configuration for testing
    TestingConfig.SESSION_TYPE = 'filesystem'
    TestingConfig.SESSION_REDIS = None
    
    app = create_app(TestingConfig)
    
    # Establish an application context
    with app.app_context():
        # Create all database tables
        db.create_all()
        yield app
        # Drop all database tables
        db.drop_all()

@pytest.fixture(scope='function')
def client(app):
    """Create a test client for making requests"""
    return app.test_client()

@pytest.fixture(scope='function')
def db_session(app):
    """Create a database session for each test"""
    connection = db.engine.connect()
    transaction = connection.begin()
    
    # Create a new session
    session = db.session
    
    yield session
    
    # Rollback the transaction
    transaction.rollback()
    connection.close()
    session.remove()

@pytest.fixture
def admin_token(app):
    """Create an admin access token for testing"""
    if not create_access_token:
        pytest.skip("JWT not installed")
    
    from app.models.user import User
    
    # Create an admin user
    admin_user = User(
        username='admin_test',
        email='admin@test.com',
        is_admin=True
    )
    
    with app.app_context():
        # Use create_access_token to generate a token
        token = create_access_token(identity=admin_user.id)
    
    return token

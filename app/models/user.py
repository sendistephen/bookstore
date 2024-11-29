from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import uuid
import re
from utils.error_handler import bad_request_error
from app.extensions import db
import secrets

# Association table for user roles
user_roles = db.Table(
    'user_roles',
    db.Column(
        'user_id',
        db.String(36),
        db.ForeignKey('users.id'),
        primary_key=True),
    db.Column(
        'role_id',
        db.String(36),
        db.ForeignKey('roles.id'),
        primary_key=True))


class User(db.Model):
    """User Model for storing user related details"""
    __tablename__ = 'users'

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(
            uuid.uuid4()))
    username = db.Column(db.String(32), unique=True, nullable=False)
    name = db.Column(db.String(32), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(512), nullable=False)
    phone = db.Column(db.String(15), unique=True, nullable=True)
    # email verification status
    is_verified = db.Column(db.Boolean, default=False)
    # account activation status
    is_active = db.Column(db.Boolean, default=True)
    # verification token
    verification_token = db.Column(db.String(500), unique=True, nullable=True)
    verification_token_expires = db.Column(db.DateTime, nullable=True)
    # password reset token
    reset_token = db.Column(db.String(500), unique=True, nullable=True)
    reset_token_expires = db.Column(db.DateTime, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow)

    # Google Oauth-related fields
    google_id = db.Column(db.String(255), unique=True, nullable=True)
    google_token = db.Column(db.String(500), nullable=True)
    google_profile_pic = db.Column(db.String(255), nullable=True)
    is_google_authenticated = db.Column(db.Boolean, nullable=False, default=False)

    # relationships
    roles = db.relationship(
        'Role',
        secondary=user_roles,
        back_populates='users',
        lazy='dynamic')

    def __repr__(self):
        return f'<User {self.username} ({self.email})>'

    @classmethod
    def validate_password(cls, password):
        """Validate password complexity"""
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        
        if not any(c.isupper() for c in password):
            return False, "Password must contain at least one uppercase letter"
            
        if not any(c.islower() for c in password):
            return False, "Password must contain at least one lowercase letter"
            
        if not any(c.isdigit() for c in password):
            return False, "Password must contain at least one number"
            
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            return False, "Password must contain at least one special character"
            
        return True, "Password is valid"

    def set_password(self, password):
        """Set password hash"""
        # Password validation is done in the service layer
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check password hash"""
        return check_password_hash(self.password_hash, password)

    def generate_verification_token(self):
        """Generate email verification token"""
        self.verification_token = secrets.token_urlsafe(32)
        self.verification_token_expires = datetime.utcnow() + timedelta(hours=24)
        db.session.commit()
        return self.verification_token

    def verify_email(self, token):
        """Verify email with token"""
        if (self.verification_token != token or
                self.verification_token_expires < datetime.utcnow()):
            return False
        self.is_verified = True
        self.verification_token = None
        self.verification_token_expires = None
        db.session.commit()
        return True

    def generate_reset_token(self):
        """Generate password reset token"""
        self.reset_token = secrets.token_urlsafe(32)
        self.reset_token_expires = datetime.utcnow() + timedelta(hours=1)
        db.session.commit()
        return self.reset_token

    def verify_reset_token(self, token):
        """Verify password reset token"""
        if (self.reset_token != token or
                self.reset_token_expires < datetime.utcnow()):
            return False
        return True

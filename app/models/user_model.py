from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid

class User(db.Model):
    """User Model for storing user related details"""
    __tablename__ = 'users'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda:str(uuid.uuid4()))  
    username = db.Column(db.String(32), unique=True, nullable=False)
    name = db.Column(db.String(32), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    phone = db.Column(db.String(15), unique=True, nullable=True)
    is_verified = db.Column(db.Boolean, default=False) # email verification status
    is_active = db.Column(db.Boolean, default=True) # account activation status
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Google Oauth-related fields
    google_id = db.Column(db.String(255), unique=True,nullable=True) # Google user ID
    google_token = db.Column(db.String(500), nullable=True) # Google Oauthtoken
    google_profile_pic = db.Column(db.String(255), nullable=True) # Google profile picture
    is_google_authenticated = db.Column(db.Boolean, nullable=False, default=False) # flag to indicate if the user is authenticated with Google
  
  
    def __repr__(self):
        return f'<User {self.username} ({self.email})>'
    
    
from app.extensions import db
import uuid
from datetime import datetime

class BookCategory(db.Model):
    """Book category model for storing book categories"""
    
    __tablename__ = 'book_categories'
    id = db.Column(db.String(32), unique=True, primary_key=True, default=lambda:str(uuid.uuid4()))
    name = db.Column(db.String(32), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self) -> dict:
        """Convert the BookCategory object to a dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    
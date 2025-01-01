from sqlalchemy import Enum
from app.extensions import db
import uuid
from datetime import datetime

class Cart(db.Model):
   
   __tablename__ = 'cart'
   
   id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
   total_items = db.Column(db.Integer, nullable=False, default=0)
   total_price = db.Column(db.Float, nullable=False, default=0.0)
   created_at = db.Column(db.DateTime, default=datetime.utcnow)
   updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
   status= db.Column(db.Enum('active', 'completed', 'cancelled', name='cart_status'), default='active')
  
   cart_items = db.relationship('CartItem', back_populates='cart', lazy='joined', cascade='all, delete-orphan')
   user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
   user = db.relationship('User', back_populates='carts')
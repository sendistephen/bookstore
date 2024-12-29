from sqlalchemy import CheckConstraint
from app.extensions import db
import uuid
from datetime import datetime

class CartItem(db.Model):
    __tablename__ = 'cart_items'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda:str(uuid.uuid4()))
    
    # Relationships
    cart_id = db.Column(db.String(36), db.ForeignKey('cart.id'), nullable=False)
    book_id = db.Column(db.String(36), db.ForeignKey('books.id'), nullable=False)
    cart = db.relationship('Cart', back_populates='cart_items', lazy='joined')
    book = db.relationship('Book', back_populates='cart_items', lazy='joined')
    
    # Tracking fields
    quantity = db.Column(db.Integer, nullable=False, default=1)
    price_at_addition = db.Column(db.Float, nullable=False)
    subtotal = db.Column(db.Float, nullable=False, default=0.0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Constraints
    __table_args__ = (
        CheckConstraint('quantity > 0',
                            name='check_positive_quantity'),
        CheckConstraint('price_at_addition >= 0',
                            name='check_non_negative_price_at_addition'),
        CheckConstraint('subtotal >= 0',
                            name='check_non_negative_subtotal'),
    )
    
    @property
    def calculate_subtotal(self):
        return self.quantity * self.price_at_addition
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Calculate subtotal on initialization
        if self.quantity is not None and self.price_at_addition is not None:
           self.subtotal = self.calculate_subtotal
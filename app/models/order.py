from app.extensions import db
from enum import Enum
from datetime import datetime
import uuid

class OrderStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    PAID = "paid"
    SHIPPED = "shipped"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class PaymentMethod(str, Enum):
    MTN_MOBILE_MONEY = "mtn_mobile_money"
    AIRTEL_MONEY = "airtel_money"
    STRIPE = "stripe"
    ORDER_ON_DELIVERY = "order_on_delivery"

class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.Enum(OrderStatus), default=OrderStatus.PENDING)
    payment_method = db.Column(db.Enum(PaymentMethod), nullable=True)
    payment_transaction_id = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Billing Information
    billing_name = db.Column(db.String(100), nullable=True, default='Unknown')
    billing_email = db.Column(db.String(100), nullable=True, default='')
    billing_phone = db.Column(db.String(20), nullable=True, default='')
    billing_street = db.Column(db.String(200), nullable=True, default='')
    billing_city = db.Column(db.String(100), nullable=True, default='')
    billing_state = db.Column(db.String(100), nullable=True, default='')
    billing_postal_code = db.Column(db.String(20), nullable=True, default='')
    billing_country = db.Column(db.String(100), nullable=True, default='')

    # Shipping Information (if different from billing)
    shipping_name = db.Column(db.String(100), nullable=True, default='')
    shipping_email = db.Column(db.String(100), nullable=True, default='')
    shipping_phone = db.Column(db.String(20), nullable=True, default='')
    shipping_street = db.Column(db.String(200), nullable=True, default='')
    shipping_city = db.Column(db.String(100), nullable=True, default='')
    shipping_state = db.Column(db.String(100), nullable=True, default='')
    shipping_postal_code = db.Column(db.String(20), nullable=True, default='')
    shipping_country = db.Column(db.String(100), nullable=True, default='')

    # Relationships
    user = db.relationship("User", back_populates="orders")
    order_items = db.relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

class OrderItem(db.Model):
    __tablename__ = 'order_items'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    order_id = db.Column(db.String(36), db.ForeignKey('orders.id'), nullable=False)
    book_id = db.Column(db.String(36), db.ForeignKey('books.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)

    # Relationships
    order = db.relationship("Order", back_populates="order_items")
    book = db.relationship("Book", back_populates="order_items")

class OrderStatusChangeLog(db.Model):
    """
    Audit log for order status changes made by admins
    """
    __tablename__ = 'order_status_change_logs'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    order_id = db.Column(db.String(36), db.ForeignKey('orders.id'), nullable=False, index=True)
    admin_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, index=True)
    
    previous_status = db.Column(db.String(50), nullable=False)
    new_status = db.Column(db.String(50), nullable=False)
    
    reason = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    order = db.relationship('Order', backref=db.backref('status_change_logs', lazy='dynamic'))
    admin = db.relationship('User', backref=db.backref('order_status_changes', lazy='dynamic'))
    
    def __repr__(self):
        return f'<OrderStatusChangeLog {self.id}: {self.previous_status} -> {self.new_status}>'

from marshmallow import Schema, fields, validate, ValidationError, post_load, validates_schema
from flask_jwt_extended import get_jwt_identity

from app.models.order import PaymentMethod, OrderStatus
from app.models.cart import Cart

class AddressSchema(Schema):
    """
    Schema for validating billing and shipping address details
    """
    name = fields.String(required=True, validate=validate.Length(min=2, max=100))
    email = fields.Email(required=True)
    phone = fields.String(required=True, validate=validate.Length(min=10, max=20))
    street = fields.String(required=False, validate=validate.Length(max=200))
    city = fields.String(required=False, validate=validate.Length(max=100))
    state = fields.String(required=False, validate=validate.Length(max=100))
    postal_code = fields.String(required=False, validate=validate.Length(max=20))
    country = fields.String(required=True, validate=validate.Length(min=2, max=100))

class OrderSchema(Schema):
    """
    Schema for creating a new order
    """
    order_id = fields.String(required=False, allow_none=True)
    payment_method = fields.Enum(PaymentMethod, by_value=True, required=True)
    cart_id = fields.String(required=True)
    transaction_id = fields.String(required=False, allow_none=True)
    
    billing_info = fields.Nested(AddressSchema, required=True)
    shipping_info = fields.Nested(AddressSchema, required=False, allow_none=True)

    @validates_schema
    def validate_shipping_info(self, data, **kwargs):
        """
        Validate that shipping info is optional
        If not provided, billing info will be used
        """
        if 'shipping_info' not in data or data['shipping_info'] is None:
            data['shipping_info'] = data['billing_info']
        return data

    @post_load
    def process_order_data(self, data, **kwargs):
        """
        Process and validate order data before creating the order
        """
        # Get user ID from JWT token
        user_id = get_jwt_identity()
        
        try:
            # Validate cart belongs to user
            cart = Cart.query.filter_by(id=data['cart_id'], user_id=user_id).first()
            
            if not cart:
                raise ValidationError('Invalid cart or cart does not belong to the user')
        except Exception as e:
            raise ValidationError(f'Error validating cart: {str(e)}')
        
        return data

class OrderQuerySchema(Schema):
    """
    Schema for order query parameters
    """
    status = fields.Enum(OrderStatus, by_value=True, required=False, allow_none=True)
    start_date = fields.Date(required=False)
    end_date = fields.Date(required=False)
    page = fields.Integer(required=False, validate=validate.Range(min=1), default=1)
    per_page = fields.Integer(required=False, validate=validate.Range(min=1, max=100), default=10)

from marshmallow import Schema, fields, validate
from app.models.order import PaymentMethod, OrderStatus

class OrderSchema(Schema):
    """
    Schema for order-related operations
    """
    order_id = fields.String(required=False, allow_none=True)
    payment_method = fields.Enum(
        PaymentMethod, 
        by_value=True, 
        required=True, 
        validate=validate.OneOf([method.value for method in PaymentMethod])
    )
    cart_id = fields.String(required=True)
    transaction_id = fields.String(required=False, allow_none=True)

class OrderQuerySchema(Schema):
    """
    Schema for order query parameters
    """
    status = fields.Enum(
        OrderStatus, 
        by_value=True, 
        required=False, 
        validate=validate.OneOf([status.value for status in OrderStatus])
    )

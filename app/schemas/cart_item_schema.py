from app.extensions import ma
from marshmallow import validate, fields
from app.models.cart_item import CartItem
from app.schemas.book_schema import BookSchema

class CartItemSchema(ma.SQLAlchemyAutoSchema):
    """Cart item schema class"""
    class Meta:
        model = CartItem
        load_instance = True
        include_fk = True
        include_relationships = True
        
    id = fields.String(dump_only=True)
    
    # Relationship fields
    cart_id = fields.String(required=True, load_only=True)
    book_id = fields.String(required=True, load_only=True)
    
    # Book details(nested schema)
    book = ma.Nested(BookSchema, only=['id','title','author','price'], dump_only=True)
    
    # Tracking fields
    quantity = fields.Integer(required=True, validate=validate.Range(min=1), 
                          error_messages={'validator_failed': 'Quantity must be at least 1'})
    price_at_addition = fields.Float(required=True, validate=validate.Range(min=0), 
                                 error_messages={'validator_failed': 'Price must be non-negative'})
    subtotal = fields.Float(dump_only=True)
    
    created_at = fields.DateTime(dump_only=True)
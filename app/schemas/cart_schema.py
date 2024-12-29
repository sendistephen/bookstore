from app.extensions import ma
from app.models.cart import Cart
from marshmallow import fields
from app.schemas.cart_item_schema import CartItemSchema

class CartSchema(ma.SQLAlchemyAutoSchema):
    """ Cart schema class for serializing and deserializing cart data """
    
    class Meta:
        model = Cart
        include_fk = True
        include_relationships = True
        load_instance = True
        
    id = ma.String(dump_only=True)
    
    # Relationship fields
    user_id = ma.String(required=True, load_only=True)
    
    # Nested relationship fields
    cart_items = ma.Nested(CartItemSchema, many=True, exclude=('cart_id',))
    
    # Tracking fields
    total_items = ma.Integer(dump_only=True)
    total_price = ma.Float(dump_only=True)
    
    status = fields.String(dump_only=True)
    created_at = ma.DateTime(dump_only=True)
    updated_at = ma.DateTime(dump_only=True)
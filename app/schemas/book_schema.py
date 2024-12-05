from app.extensions import ma
from marshmallow import validate
from app.models.book import Book
from app.schemas.book_category_schema import BookCategorySchema

class BookSchema(ma.SQLAlchemyAutoSchema):
    """Book schema class"""
    class Meta:
        model = Book
        load_instance = True
        include_fk = True
        include_relationships = True
    
    # Add validation for fields
    title = ma.String(required=True, validate=validate.Length(min=2, max=100))
    isbn = ma.String(required=True, validate=validate.Length(equal=13))
    price = ma.Float(required=True, validate=validate.Range(min=0))
    stock_quantity = ma.Integer(required=True, validate=validate.Range(min=0))
    
    # Include nested category information
    category = ma.Nested(BookCategorySchema, dump_only=True)
    category_id = ma.String(required=True, load_only=True)
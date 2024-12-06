from app.extensions import ma
from marshmallow import validate, pre_load
from app.models.book import Book
from app.schemas.book_category_schema import BookCategorySchema
from app.schemas.author_schema import AuthorSchema

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
    description = ma.String(required=False, allow_none=True)
    price = ma.Float(required=True, validate=validate.Range(min=0))
    stock_quantity = ma.Integer(required=True, validate=validate.Range(min=0))
    
    # Include nested category and author information
    category = ma.Nested(BookCategorySchema, dump_only=True)
    author = ma.Nested('AuthorSchema', exclude=('authored_books',), dump_only=True)
    category_id = ma.String(required=True, load_only=True)

    @pre_load
    def remove_none_values(self, data, **kwargs):
        """Remove None values to allow partial updates"""
        return {k: v for k, v in data.items() if v is not None}


class BookUpdateSchema(ma.SQLAlchemyAutoSchema):
    """Book update schema class"""
    class Meta:
        model = Book
        load_instance = True
        include_fk = True
        include_relationships = True
        partial = True  # Allow partial updates

    # Optional fields for update
    title = ma.String(required=False, validate=validate.Length(min=2, max=100))
    isbn = ma.String(required=False, validate=validate.Length(equal=13))
    description = ma.String(required=False, allow_none=True)
    price = ma.Float(required=False, validate=validate.Range(min=0))
    stock_quantity = ma.Integer(required=False, validate=validate.Range(min=0))
    category_id = ma.String(required=False)

    @pre_load
    def remove_none_values(self, data, **kwargs):
        """Remove None values to allow partial updates"""
        return {k: v for k, v in data.items() if v is not None}
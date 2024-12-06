from app.extensions import ma
from marshmallow import validate,validates
from app.models.author import Author

class AuthorSchema(ma.SQLAlchemyAutoSchema):
    """Schema for validating Author and serializing Author data"""
    class Meta:
        model = Author
        load_instance = True
        include_relationships = True

    name = ma.String(required=True, validate=validate.Length(min=2, max=100))
    biography = ma.String(required=False, validate=validate.Length(max=1000))
    
    # Nested serialzation of books
    # Use a string reference to avoid circular import
    authored_books = ma.Nested('BookSchema', many=True, exclude=('author',), dump_only=True)
    
    created_at = ma.DateTime(dump_only=True)
    updated_at = ma.DateTime(dump_only=True)
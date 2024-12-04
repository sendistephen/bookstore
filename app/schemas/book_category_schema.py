from marshmallow import Schema, fields, validate, validates, validates_schema
from marshmallow.exceptions import ValidationError
from app.models.book_category import BookCategory
from utils.error_handler import bad_request_error

class BookCategorySchema(Schema):
    """Schema for book category"""
    id = fields.Str(dump_only=True) 
    name = fields.Str(required=True, validate=[
        validate.Length(min=2, max=50, error="Name must be between 2 and 50 characters"),
        validate.Regexp(
            regex=r"^[A-Za-z ]+$",
            error="Name must contain only letters and spaces"
        )
    ])
    description = fields.Str(required=False, allow_none=True, validate=[
        validate.Length(
            min=2,
            max=100,
            error="Description must be between 2 and 100 characters"
        )
    ])
    book_count = fields.Int(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    
    @validates('name')
    def validate_name(self, name):
        """Validate that category name is unique"""
        if BookCategory.query.filter_by(name=name).first():
            raise ValidationError('Book category already exists')
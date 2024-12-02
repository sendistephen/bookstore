from marshmallow import Schema, fields, validate, validates, validates_schema
from marshmallow.exceptions import ValidationError
from app.models.book_category import BookCategory
from utils.error_handler import bad_request_error

class BookCategorySchema(Schema):
    """Schema for book category"""
    id = fields.Str(dump_only=True) 
    name = fields.Str(required=True, validate=[
        validate.Length(min=2, max=32,error="Name must be between 2 and 32 characters"),
        validate.Regexp(
            regex=r"^[A-Za-z  ]+$",
            error="Name must contain only letters and spaces"
        )
    ])
    description = fields.Str(required=False, allow_none=True, validate=validate.Length(
        min=2,
        max=100,
        error="Description must be between 2 and 100 characters"
    ))
    book_count = fields.Int(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    
    @validates_schema
    def validate_name(self, data, **kwargs):
        """Validate that category name is unique"""
        name = data.get('name')
        if name and  BookCategory.query.filter_by(name=name).first():
            raise ValidationError('Book category already exists')
        
    #
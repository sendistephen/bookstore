from marshmallow import Schema, fields, validate, validates, validates_schema
from marshmallow.exceptions import ValidationError
from app.models.book_category import BookCategory
from utils.error_handler import bad_request_error
import logging

class BookCategorySchema(Schema):
    """Schema for book category"""
    id = fields.Str(dump_only=True) 
    name = fields.Str(required=False, validate=[
        validate.Length(min=2, max=50, error="Name must be between 2 and 50 characters"),
        validate.Regexp(
            regex=r"^[A-Za-z0-9 \-_]+$",
            error="Name must contain letters, numbers, spaces, hyphens, or underscores"
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
        logging.info(f"Validating name: {name}")
        if not name:
            logging.info("Name is empty or None, skipping unique check")
            return
        
        # Check if the name is being used by another category
        existing = BookCategory.query.filter_by(name=name).first()
        if existing and existing.id != self.context.get('category_id'):
            logging.error(f"Duplicate name found: {name}")
            raise ValidationError('Book category already exists')

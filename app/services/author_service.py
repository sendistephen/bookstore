from flask import current_app
from app.models.author import Author
from app.extensions import db
from app.schemas.author_schema import AuthorSchema
from marshmallow.exceptions import ValidationError

class AuthorService:
    """Author service class"""
    
    @staticmethod
    def get_author(author_id):
        """Get an author by ID"""
        pass
    
    @staticmethod
    def get_books_by_author(author_id):
        """Get books by author"""
        pass
    
    @staticmethod
    def check_author_exists(payload):
        """Check if an author with the given name exists"""
        if 'name' in payload:
            existing_author = Author.query.filter_by(name=payload['name']).first()
            if existing_author:
                return True, f"Author with name {payload['name']} already exists"
        return False, None
       
        
    @staticmethod
    def create_author(payload):
        """Create a new author"""
        try:
            # Initialize schema
            author_schema = AuthorSchema()
            
            # Validate and deserialize input
            author_data = author_schema.load(payload, session=db.session)
            
            # Create new author instance
            new_author = Author(
                name=author_data.name,
                biography=author_data.biography
            )
            
            # Add to database
            db.session.add(new_author)
            db.session.commit()
            
            # Return serialized author
            return author_schema.dump(new_author), None
        
        except ValidationError as ve:
            current_app.logger.error(f"Author validation error: {ve.messages}")
            db.session.rollback()
            return None, ve.messages
        
        except Exception as e:
            current_app.logger.error(f"Author creation error: {str(e)}")
            db.session.rollback()
            return None, str(e)
    
    @staticmethod
    def update_author(author_id, name, biography):
        """Update an author"""
        pass
    
    @staticmethod
    def delete_author(author_id):
        """Delete an author"""
        pass
    
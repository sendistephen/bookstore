from utils.error_handler import bad_request_error
from app.models.book_category import BookCategory
from flask import current_app
from app.extensions import db

class BookCategoryService:
    """Book category service"""
    
    @staticmethod
    def get_all_book_categories():
        """
        Get all book categories

        Returns:
            List[BookCategory]: List of book categories
        
        Raises:
            Exception: If there's an error fetching book categories
        """
        try:
            # Fetch all categories, ordered by name
            categories = BookCategory.query.order_by(BookCategory.name).all()
            
            # If no categories exist, return an empty list
            if not categories:
                current_app.logger.info("No book categories found")
            
            return categories
        
        except Exception as e:
            # Log the specific error for debugging
            current_app.logger.error(f"Error fetching book categories: {str(e)}")
            
            # Re-raise the exception to be handled by the caller
            raise
    
    @staticmethod
    def create_book_category(name:str, description:str=None):
        """ Create a new book category """
        try:
            # normalize payload
            name = name.strip()
            description = description.strip() if description else None
            
            # check if category already exists
            existing_category = BookCategory.query.filter_by(name=name).first()
            
            if existing_category:
                raise ValueError(f'Category "{name}" already exists')
            
            # Create a new category
            new_category = BookCategory(name=name, description=description)
            
            # Add and commit the new category
            db.session.add(new_category)
            db.session.commit()
            
            return new_category
        
        except Exception as e:
            # Rollback the transaction in case of an error
            db.session.rollback()
            
            # Log the specific error for debugging
            current_app.logger.error(f"Error creating book category: {str(e)}")
            
            
            # Re-raise the exception to be handled by the caller
            raise
                
from utils.error_handler import bad_request_error
from app.models.book_category import BookCategory
from flask import current_app

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
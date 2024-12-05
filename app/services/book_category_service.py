from utils.error_handler import bad_request_error
from app.models.book_category import BookCategory
from flask import current_app
from app.extensions import db
from datetime import datetime

class BookCategoryService:
    """
    Service class for managing book categories.
    Handles database operations and business logic for book categories.
    """

    @staticmethod
    def get_all_book_categories():
        """
        Retrieve all book categories from the database.
        
        Returns:
            List[BookCategory]: List of all book categories
        
        Raises:
            Exception: Database query error
        """
        try:
            return BookCategory.query.all()
        except Exception as e:
            current_app.logger.error(f"Database error: {str(e)}")
            raise

    @staticmethod
    def create_book_category(name: str, description: str = None):
        """
        Create a new book category in the database.
        
        Args:
            name: Category name, must be unique
            description: Optional category description
        
        Returns:
            BookCategory: Newly created category
        
        Raises:
            ValueError: If category with name already exists
            Exception: Database error
        """
        try:
            # Check if category with same name exists
            existing_category = BookCategory.query.filter_by(name=name.strip()).first()
            if existing_category:
                raise ValueError(f"Category with name '{name}' already exists")

            # Create new category
            new_category = BookCategory(
                name=name.strip(),
                description=description.strip() if description else None
            )
            
            db.session.add(new_category)
            db.session.commit()
            
            return new_category
            
        except Exception as e:
            db.session.rollback()
            raise

    @staticmethod
    def update_book_category(category_id: str, update_data: dict):
        """
        Update an existing book category.
        
        Args:
            category_id: ID of category to update
            update_data: Dictionary containing update information
        
        Returns:
            BookCategory: Updated category
        
        Raises:
            ValueError: Category not found or update fails
            Exception: Database error
        """
        try:
            # Log the received update data
            current_app.logger.info(f"Updating category {category_id} with data: {update_data}")
            
            # Check if category exists
            existing_category = BookCategory.query.filter_by(id=category_id).first()
            
            if not existing_category:
                raise ValueError(f'Category with ID "{category_id}" not found')
            
            # Check if name is being updated
            if 'name' in update_data and update_data['name']:
                new_name = update_data['name'].strip()
                
                # Check if the new name already exists for a different category
                existing_name = BookCategory.query.filter(
                    BookCategory.name == new_name, 
                    BookCategory.id != category_id
                ).first()
                
                if existing_name:
                    # If the name already exists for another category, return the existing category
                    current_app.logger.info(f"Category with name '{new_name}' already exists")
                    return existing_category
                
                # Update the name
                existing_category.name = new_name
            
            # Update description if provided
            if 'description' in update_data:
                description = update_data['description']
                existing_category.description = description.strip() if description else None
            
            # Update timestamps
            existing_category.updated_at = datetime.utcnow()
            
            # Commit the changes
            db.session.commit()
            
            current_app.logger.info(f"Successfully updated category {category_id}")
            
            return existing_category
        
        except Exception as e:
            # Log the specific error for debugging
            current_app.logger.error(f"Error updating book category: {str(e)}")
            
            # Rollback the transaction in case of an error
            db.session.rollback()
            
            # Re-raise the exception to be handled by the caller
            raise

    @staticmethod
    def replace_book_category(category_id: str, replacement_data: dict):
        """
        Replace all fields of an existing book category.
        
        Args:
            category_id: ID of category to replace
            replacement_data: New category data containing name and description
        
        Returns:
            BookCategory: Updated category
        
        Raises:
            ValueError: Category not found or name already exists
            Exception: Database error
        """
        try:
            # Check if category exists
            existing_category = BookCategory.query.filter_by(id=category_id).first()
            if not existing_category:
                raise ValueError(f'Category with ID "{category_id}" not found')
            
            # Check if new name already exists
            new_name = replacement_data.get('name', '').strip()
            if new_name:
                name_exists = BookCategory.query.filter(
                    BookCategory.name == new_name,
                    BookCategory.id != category_id
                ).first()
                
                if name_exists:
                    raise ValueError(f"Category with name '{new_name}' already exists")
            
            # Update category data
            existing_category.name = new_name
            existing_category.description = replacement_data.get('description', '').strip() or None
            existing_category.updated_at = datetime.utcnow()
            
            db.session.commit()
            return existing_category
            
        except Exception as e:
            db.session.rollback()
            raise

    @staticmethod
    def delete_book_category(category_id: str):
        """
        Delete a book category from the database.
        
        Args:
            category_id: ID of category to delete
        
        Returns:
            bool: True if deletion successful
        
        Raises:
            ValueError: Category not found
            Exception: Database error
        """
        try:
            # Check if category exists
            category = BookCategory.query.filter_by(id=category_id).first()
            if not category:
                raise ValueError(f'Category with ID "{category_id}" not found')
            #TODO: if a category has books dont delete raise an error
            
            db.session.delete(category)
            db.session.commit()
            return True
            
        except Exception as e:
            db.session.rollback()
            raise
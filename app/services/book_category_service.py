from utils.error_handler import bad_request_error
from app.models.book_category import BookCategory
from flask import current_app
from app.extensions import db
from datetime import datetime

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
    
    @staticmethod
    def update_book_category(category_id:str, update_data:dict):
        """
        Update an existing book category
        
        Args:
            category_id (str): ID of the category to update
            update_data (dict): Dictionary containing update information
        
        Returns:
            BookCategory: Updated book category
        
        Raises:
            ValueError: If category not found or update fails
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
    def replace_book_category(category_id:str, replacement_data:dict):
        """
        Replace an existing book category with new data
        
        Args:
            category_id (str): ID of the category to replace
            replacement_data (dict): Dictionary containing replacement information
        
        Returns:
            BookCategory: Replaced book category
        
        Raises:
            ValueError: If category not found or replacement fails
        """
        try:
            # Log the received replacement data
            current_app.logger.info(f"Replacing category {category_id} with data: {replacement_data}")
            
            # Check if category exists
            existing_category = BookCategory.query.filter_by(id=category_id).first()
            
            if not existing_category:
                raise ValueError(f'Category with ID "{category_id}" not found')
            
            # Check if the new name already exists for another category
            new_name = replacement_data.get('name', '').strip()
            if new_name:
                existing_name = BookCategory.query.filter(
                    BookCategory.name == new_name, 
                    BookCategory.id != category_id
                ).first()
                
                if existing_name:
                    # If the name already exists for another category, raise an error
                    raise ValueError(f"Category with name '{new_name}' already exists")
            
            # Replace the category data
            existing_category.name = new_name
            existing_category.description = replacement_data.get('description', '').strip() or None
            
            # Update timestamps
            existing_category.updated_at = datetime.utcnow()
            
            # Commit the changes
            db.session.commit()
            
            current_app.logger.info(f"Successfully replaced category {category_id}")
            
            return existing_category
        
        except Exception as e:
            # Log the specific error for debugging
            current_app.logger.error(f"Error replacing book category: {str(e)}")
            
            # Rollback the transaction in case of an error
            db.session.rollback()
            
            # Re-raise the exception to be handled by the caller
            raise
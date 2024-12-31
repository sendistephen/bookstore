import os
import uuid
import logging

logger = logging.getLogger(__name__)

try:
    import cloudinary
    from cloudinary.uploader import upload, destroy
except ImportError:
    logger.warning("Cloudinary module not installed. Image uploads will fail.")
    cloudinary = None
    upload = None
    destroy = None

from flask import current_app
from werkzeug.utils import secure_filename
from app.extensions import db
from app.models.book import Book

class BookImageService:
    """Service for handling book cover image uploads and management"""

    @staticmethod
    def configure_cloudinary():
        """
        Configure Cloudinary with environment variables
        
        Raises:
            ValueError: If Cloudinary credentials are not configured
        """
        cloud_name = current_app.config.get('CLOUDINARY_CLOUD_NAME')
        api_key = current_app.config.get('CLOUDINARY_API_KEY')
        api_secret = current_app.config.get('CLOUDINARY_API_SECRET')
        
        current_app.logger.info(f"Cloudinary Config - Cloud Name: {cloud_name}")
        current_app.logger.info(f"Cloudinary Config - API Key: {api_key}")
        
        if not all([cloud_name, api_key, api_secret]):
            current_app.logger.error("Cloudinary credentials are incomplete")
            raise ValueError("Cloudinary credentials are not fully configured")
        
        if cloudinary:
            cloudinary.config(
                cloud_name=cloud_name,
                api_key=api_key,
                api_secret=api_secret
            )
        else:
            current_app.logger.error("Cloudinary module is not imported")

    @staticmethod
    def validate_image_file(file):
        """
        Validate uploaded image file
        
        Args:
            file (FileStorage): Uploaded file
        
        Raises:
            ValueError: If file is invalid
        """
        allowed_extensions = {'png', 'jpg', 'jpeg', 'webp'}
        max_file_size = 5 * 1024 * 1024  # 5MB
        
        # Check if file is empty
        if not file or file.filename == '':
            raise ValueError("No file uploaded")
        
        # Check file extension
        file_ext = file.filename.rsplit('.', 1)[1].lower()
        if file_ext not in allowed_extensions:
            raise ValueError(f"Invalid file type. Allowed types: {', '.join(allowed_extensions)}")
        
        # Check file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > max_file_size:
            raise ValueError(f"File too large. Maximum size is {max_file_size / 1024 / 1024}MB")

    @staticmethod
    def generate_public_id(book_id, cover_type='front', original_filename=None):
        """
        Generate a consistent and clean public ID for Cloudinary
        
        Args:
            book_id (str): Unique book identifier
            cover_type (str): 'front' or 'back'
            original_filename (str, optional): Original filename for extension
        
        Returns:
            str: Unique public ID for the image
        """
        # Validate cover type
        if cover_type not in ['front', 'back']:
            raise ValueError("Cover type must be 'front' or 'back'")
        
        # Generate unique identifier
        unique_id = str(uuid.uuid4())
        
        # Determine file extension
        file_ext = ''
        if original_filename:
            # Use os.path to split extension correctly
            ext = os.path.splitext(original_filename)[1].lower()
            # Remove leading dot and ensure single extension
            file_ext = ext.lstrip('.')
            
            # Normalize common image extensions
            ext_map = {
                'jpeg': 'jpg',
                'jpe': 'jpg',
                'tiff': 'tif'
            }
            file_ext = ext_map.get(file_ext, file_ext)
        
        # Construct clean, consistent path
        # Use the extracted extension or an empty string
        base_path = f"bookstore/books/{book_id}/{cover_type}_cover_{unique_id}"
        return f"{base_path}.{file_ext}" if file_ext else base_path

    @staticmethod
    def upload_book_cover(book_id, file, cover_type='front'):
        """
        Upload book cover image to Cloudinary
        
        Args:
            book_id (str): ID of the book
            file (FileStorage): Uploaded image file
            cover_type (str): 'front' or 'back' cover
        
        Returns:
            dict: Upload result with URL and public ID
        """
        # Extensive logging for debugging
        current_app.logger.info(f"Starting book cover upload - Book ID: {book_id}, Cover Type: {cover_type}")
        current_app.logger.info(f"File details - Name: {file.filename}, Content Type: {file.content_type}")
        
        # Find the book
        book = Book.query.get(book_id)
        if not book:
            current_app.logger.error(f"Book not found with ID: {book_id}")
            raise ValueError(f"Book with ID {book_id} not found")
        
        # Validate image file
        try:
            BookImageService.validate_image_file(file)
        except ValueError as validation_error:
            current_app.logger.error(f"Image validation failed: {str(validation_error)}")
            raise
        
        # Configure Cloudinary
        try:
            BookImageService.configure_cloudinary()
        except Exception as config_error:
            current_app.logger.error(f"Cloudinary configuration error: {str(config_error)}")
            raise ValueError("Failed to configure Cloudinary")
        
        # Generate unique public ID
        public_id = BookImageService.generate_public_id(
            book_id, 
            cover_type, 
            file.filename
        )
        current_app.logger.info(f"Generated Public ID: {public_id}")
        
        # Upload to Cloudinary with transformations
        try:
            if upload:
                # Ensure file is at the beginning of the stream
                file.seek(0)
                
                upload_result = upload(
                    file,
                    public_id=public_id,
                    folder="bookstore",  # Root folder in Cloudinary
                    transformation=[
                        {'width': 800, 'height': 1200, 'crop': 'limit'},
                        {'quality': 'auto:good'}
                    ],
                    resource_type='image'
                )
                
                current_app.logger.info(f"Cloudinary upload successful - URL: {upload_result.get('secure_url')}")
            else:
                current_app.logger.error("Cloudinary upload function is not available")
                raise ValueError("Cloudinary upload function is not available")
        except Exception as e:
            current_app.logger.error(f"Cloudinary upload error: {str(e)}")
            raise ValueError(f"Failed to upload image to Cloudinary: {str(e)}")
        
        # Update book model
        try:
            if cover_type == 'front':
                book.front_cover_url = upload_result['secure_url']
                book.front_cover_public_id = upload_result['public_id']
            else:
                book.back_cover_url = upload_result['secure_url']
                book.back_cover_public_id = upload_result['public_id']
            
            db.session.commit()
            current_app.logger.info(f"Book cover updated successfully for book {book_id}")
        except Exception as e:
            current_app.logger.error(f"Database update error: {str(e)}")
            db.session.rollback()
            raise ValueError("Failed to save image information")
        
        return {
            'url': upload_result['secure_url'],
            'public_id': upload_result['public_id']
        }

    @staticmethod
    def delete_image(public_id):
        """
        Delete an image from Cloudinary
        
        Args:
            public_id (str): Cloudinary public ID of the image
        
        Returns:
            dict: Deletion result from Cloudinary
        """
        if not public_id:
            return None
        
        # Configure Cloudinary
        BookImageService.configure_cloudinary()
        
        try:
            if destroy:
                return destroy(public_id)
            else:
                raise ValueError("Cloudinary destroy function is not available")
        except Exception as e:
            current_app.logger.error(f"Cloudinary deletion error: {str(e)}")
            return None

    @staticmethod
    def get_book_covers(book_id):
        """
        Retrieve book cover URLs
        
        Args:
            book_id (str): ID of the book
        
        Returns:
            dict: URLs for front and back covers
        """
        book = Book.query.get(book_id)
        if not book:
            raise ValueError(f"Book with ID {book_id} not found")
        
        return {
            'front_cover': book.front_cover_url,
            'back_cover': book.back_cover_url
        }
from flask import request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.api.v1 import bp
from app.services.book_image_service import BookImageService
from app.models.book import Book
from app.extensions import db
from app.services.auth_service import AuthService

@bp.route('/books/<book_id>/covers', methods=['POST', 'GET', 'DELETE'])
@jwt_required()
def book_covers(book_id):
    """
    Manage book cover images
    - POST: Upload a book cover
    - GET: Retrieve book cover URLs
    - DELETE: Remove a book cover
    """
    # Log incoming request details
    current_app.logger.info(f"Incoming request - Method: {request.method}, Book ID: {book_id}")
    current_app.logger.info(f"Request content type: {request.content_type}")
    current_app.logger.info(f"Request files: {request.files}")
    current_app.logger.info(f"Request form: {request.form}")
    current_app.logger.info(f"Request data: {request.data}")
    
    # Verify user's permission to access this book
    current_user_id = get_jwt_identity()
    book = Book.query.get_or_404(book_id)
    
    # Determine cover type from query parameter
    cover_type = request.args.get('cover_type', 'front')
    current_app.logger.info(f"Cover type: {cover_type}")
    
    # Handle different HTTP methods
    if request.method == 'POST':
        # Comprehensive file check
        current_app.logger.info(f"Files in request: {request.files}")
        
        # Check different ways a file might be uploaded
        uploaded_file = None
        if 'file' in request.files:
            uploaded_file = request.files['file']
            current_app.logger.info(f"File found with key 'file': {uploaded_file.filename}")
        elif len(request.files) > 0:
            # If no 'file' key, log all available keys
            for key, file in request.files.items():
                current_app.logger.info(f"Alternative file key found: {key}, filename: {file.filename}")
                uploaded_file = file
                break
        
        # If no file found
        if not uploaded_file:
            current_app.logger.error("No file found in the request")
            return jsonify({
                "error": "No file uploaded", 
                "details": {
                    "files": list(request.files.keys()),
                    "form": list(request.form.keys()),
                    "content_type": request.content_type
                }
            }), 400
        
        current_app.logger.info(f"Received file - Name: {uploaded_file.filename}, Content Type: {uploaded_file.content_type}")
        
        # Upload book cover
        try:
            result = BookImageService.upload_book_cover(book_id, uploaded_file, cover_type)
            return jsonify(result), 201
        except ValueError as e:
            current_app.logger.error(f"Upload error: {str(e)}")
            return jsonify({"error": str(e)}), 400
    
    elif request.method == 'GET':
        # Retrieve cover URLs
        covers = {
            'front_cover': book.front_cover_url,
            'back_cover': book.back_cover_url
        }
        return jsonify(covers), 200
    
    elif request.method == 'DELETE':
        try:
            # Determine which cover to delete based on cover_type
            if cover_type == 'front':
                public_id = book.front_cover_public_id
                book.front_cover_url = None
                book.front_cover_public_id = None
            elif cover_type == 'back':
                public_id = book.back_cover_public_id
                book.back_cover_url = None
                book.back_cover_public_id = None
            else:
                current_app.logger.error("Invalid cover type")
                return jsonify({"error": "Invalid cover type"}), 400
            
            # Delete from Cloudinary if public_id exists
            if public_id:
                BookImageService.delete_image(public_id)
            
            # Commit changes to database
            db.session.commit()
            
            current_app.logger.info(f"{cover_type.capitalize()} cover successfully deleted")
            return jsonify({
                "message": f"{cover_type.capitalize()} cover successfully deleted", 
                "book_id": book_id
            }), 200
        
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Delete error: {str(e)}")
            return jsonify({"error": str(e)}), 500

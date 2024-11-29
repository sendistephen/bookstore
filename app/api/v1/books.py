from flask import request, jsonify
from app.api.v1 import bp
from app.api.v1.auth import token_required
from utils.error_handler import bad_request_error, internal_server_error


@bp.route('/books', methods=['GET'])
@token_required
def get_books(current_user):
    """Get list of books"""
    try:
        # TODO: Implement book listing logic
        return jsonify({
            'message': 'Book listing endpoint - To be implemented'
        }), 200
    except Exception as e:
        return internal_server_error(str(e))

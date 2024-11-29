from flask import jsonify
from app.api.v1 import bp
from app.api.v1.auth import token_required


@bp.route('/users/me', methods=['GET'])
@token_required
def get_current_user(current_user):
    """Get current user profile"""
    try:
        return jsonify({
            'id': current_user.id,
            'username': current_user.username,
            'email': current_user.email,
            'is_verified': current_user.is_verified,
            'created_at': current_user.created_at.isoformat()
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

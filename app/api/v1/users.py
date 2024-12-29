from flask import jsonify
from app.api.v1 import bp
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.user import User
from utils.error_handler import unauthorized_error, internal_server_error


@bp.route('/users/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Get current user profile"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        if not current_user:
            return unauthorized_error('User not found')
            
        return jsonify({
            'status': 'success',
            'data': {
                'user': {
                    'id': current_user.id,
                    'username': current_user.username,
                    'email': current_user.email,
                    'is_verified': current_user.is_verified,
                    'roles': [role.name for role in current_user.roles],
                    'created_at': current_user.created_at.isoformat()
                }
            }
        }), 200
    except Exception as e:
        return internal_server_error(str(e))

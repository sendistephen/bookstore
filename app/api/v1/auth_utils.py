from functools import wraps
from flask_jwt_extended import verify_jwt_in_request, get_jwt
from utils.error_handler import unauthorized_error

def admin_required():
    """
    Decorator to check if the current user has admin role.
    Must be used after @jwt_required()
    """
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            roles = claims.get('roles', [])
            
            if 'admin' not in roles:
                return unauthorized_error('Admin access required')
            
            return fn(*args, **kwargs)
        return decorator
    return wrapper

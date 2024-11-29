from flask import request, jsonify, current_app, url_for
from app.api.v1 import bp
from app.schemas.user_schema import (
    UserRegistrationSchema, 
    UserLoginSchema,
    PasswordResetRequestSchema,
    PasswordResetSchema,
    PasswordChangeSchema
)
from app.services.auth_service import AuthService
from app.services.email_service import (
    send_verification_email,
    send_password_reset_email,
    send_password_changed_email
)
from utils.error_handler import bad_request_error, internal_server_error
from functools import wraps


def token_required(f):
    """Decorator to check valid token"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]
            except IndexError:
                return bad_request_error('Invalid token format')
        
        if not token:
            return bad_request_error('Token is missing')
            
        try:
            current_user = AuthService.verify_token(token)
            return f(current_user, *args, **kwargs)
        except ValueError as e:
            return bad_request_error(str(e))
            
    return decorated


@bp.route('/auth/register', methods=['POST'])
def register():
    """User registration endpoint"""
    try:
        # Validate request data
        schema = UserRegistrationSchema()
        errors = schema.validate(request.json)
        if errors:
            return bad_request_error(errors)
        
        # Register user
        user = AuthService.register_user(request.json)
        
        return jsonify({
            'message': 'Registration successful. Please check your email to verify your account.',
            'user_id': user.id
        }), 201
        
    except ValueError as e:
        return bad_request_error(str(e))
    except Exception as e:
        current_app.logger.error(f"Registration error: {str(e)}")
        return internal_server_error('Error during registration')


@bp.route('/auth/login', methods=['POST'])
def login():
    """User login endpoint"""
    try:
        # Validate request data
        schema = UserLoginSchema()
        errors = schema.validate(request.json)
        if errors:
            return bad_request_error(errors)
        
        # Login user
        result = AuthService.login_user(
            request.json['email'],
            request.json['password']
        )
        
        return jsonify(result), 200
        
    except ValueError as e:
        return bad_request_error(str(e))
    except Exception as e:
        current_app.logger.error(f"Login error: {str(e)}")
        return internal_server_error('Error during login')


@bp.route('/auth/verify-email/<token>', methods=['GET'])
def verify_email(token):
    """Verify email with token"""
    try:
        user = AuthService.verify_email(token)
        return jsonify({
            'message': 'Email verified successfully',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'name': user.name
            }
        }), 200
    except ValueError as e:
        return bad_request_error(str(e))
    except Exception as e:
        current_app.logger.error(f"Email verification error: {str(e)}")
        return internal_server_error('Error verifying email')


@bp.route('/auth/resend-verification', methods=['POST'])
@token_required
def resend_verification(current_user):
    """Resend verification email"""
    try:
        if current_user.is_verified:
            return bad_request_error('Email already verified')
            
        token = current_user.generate_verification_token()
        verification_url = url_for('api_v1.verify_email', token=token, _external=True)
        send_verification_email(current_user, verification_url)
        
        return jsonify({
            'message': 'Verification email sent successfully'
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error resending verification: {str(e)}")
        return internal_server_error('Error sending verification email')


@bp.route('/auth/forgot-password', methods=['POST'])
def forgot_password():
    """Initiate password reset"""
    try:
        schema = PasswordResetRequestSchema()
        errors = schema.validate(request.json)
        if errors:
            return bad_request_error(errors)
            
        email = request.json['email']
        AuthService.initiate_password_reset(email)
        
        # Always return success to prevent email enumeration
        return jsonify({
            'message': 'If your email is registered, you will receive password reset instructions'
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Password reset error: {str(e)}")
        return internal_server_error('Error processing password reset')


@bp.route('/auth/reset-password/<token>', methods=['POST'])
def reset_password(token):
    """Reset password with token"""
    try:
        schema = PasswordResetSchema()
        errors = schema.validate(request.json)
        if errors:
            return bad_request_error(errors)
            
        new_password = request.json['new_password']
        AuthService.reset_password(token, new_password)
        
        return jsonify({
            'message': 'Password has been reset successfully'
        }), 200
        
    except ValueError as e:
        return bad_request_error(str(e))
    except Exception as e:
        current_app.logger.error(f"Password reset error: {str(e)}")
        return internal_server_error('Error resetting password')


@bp.route('/auth/change-password', methods=['POST'])
@token_required
def change_password(current_user):
    """Change password for logged in user"""
    try:
        schema = PasswordChangeSchema()
        errors = schema.validate(request.json)
        if errors:
            return bad_request_error(errors)
            
        current_password = request.json['current_password']
        new_password = request.json['new_password']
        
        AuthService.change_password(
            current_user.id,
            current_password,
            new_password
        )
        
        # Send notification email
        device_info = {
            'device': request.user_agent.string,
            'location': request.remote_addr
        }
        send_password_changed_email(current_user, device_info)
        
        return jsonify({
            'message': 'Password changed successfully'
        }), 200
        
    except ValueError as e:
        return bad_request_error(str(e))
    except Exception as e:
        current_app.logger.error(f"Password change error: {str(e)}")
        return internal_server_error('Error changing password')


@bp.route('/auth/cleanup', methods=['POST'])
def cleanup_user():
    """Cleanup user by email"""
    try:
        data = request.get_json()
        if not data or 'email' not in data:
            return bad_request_error('Email is required')
            
        success = AuthService.delete_user_by_email(data['email'])
        if success:
            return jsonify({'message': 'User deleted successfully'}), 200
        return jsonify({'message': 'User not found'}), 404
        
    except Exception as e:
        return jsonify({'message': str(e)}), 500

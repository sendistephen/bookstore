from flask import request, jsonify, current_app, url_for, session, redirect
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
from app.services.google_auth_service import GoogleAuthService
from utils.error_handler import bad_request_error, internal_server_error, unauthorized_error
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt, create_access_token
import logging
import os

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
        result = AuthService.register_user(request.json)
        return jsonify(result), 201
        
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
        result = AuthService.verify_email(token)
        return jsonify(result), 200
    except ValueError as e:
        return bad_request_error(str(e))
    except Exception as e:
        current_app.logger.error(f"Email verification error: {str(e)}")
        return internal_server_error('Error during email verification')

@bp.route('/auth/resend-verification', methods=['POST'])
@jwt_required()
def resend_verification():
    """Resend verification email"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        if not user:
            return unauthorized_error('User not found')
            
        result = AuthService.resend_verification(user)
        return jsonify(result), 200
    except ValueError as e:
        return bad_request_error(str(e))
    except Exception as e:
        current_app.logger.error(f"Resend verification error: {str(e)}")
        return internal_server_error('Error resending verification email')

@bp.route('/auth/forgot-password', methods=['POST'])
def forgot_password():
    """Initiate password reset"""
    try:
        schema = PasswordResetRequestSchema()
        errors = schema.validate(request.json)
        if errors:
            return bad_request_error(errors)
            
        result = AuthService.request_password_reset(request.json['email'])
        return jsonify(result), 200
    except ValueError as e:
        return bad_request_error(str(e))
    except Exception as e:
        current_app.logger.error(f"Password reset request error: {str(e)}")
        return internal_server_error('Error requesting password reset')

@bp.route('/auth/reset-password/<token>', methods=['POST'])
def reset_password(token):
    """Reset password with token"""
    try:
        schema = PasswordResetSchema()
        errors = schema.validate(request.json)
        if errors:
            return bad_request_error(errors)
            
        result = AuthService.reset_password(token, request.json['new_password'])
        return jsonify(result), 200
    except ValueError as e:
        return bad_request_error(str(e))
    except Exception as e:
        current_app.logger.error(f"Password reset error: {str(e)}")
        return internal_server_error('Error resetting password')

@bp.route('/auth/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """Change password for logged in user"""
    try:
        schema = PasswordChangeSchema()
        errors = schema.validate(request.json)
        if errors:
            return bad_request_error(errors)
            
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        if not user:
            return unauthorized_error('User not found')
            
        result = AuthService.change_password(
            user,
            request.json['current_password'],
            request.json['new_password']
        )
        return jsonify(result), 200
    except ValueError as e:
        return bad_request_error(str(e))
    except Exception as e:
        current_app.logger.error(f"Password change error: {str(e)}")
        return internal_server_error('Error changing password')

@bp.route('/auth/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        if not user:
            return unauthorized_error('User not found')
            
        access_token = create_access_token(
            identity=user.id,
            additional_claims={
                'email': user.email,
                'roles': [role.name for role in user.roles]
            }
        )
        
        return jsonify({
            'status': 'success',
            'message': 'Token refreshed successfully',
            'data': {
                'access_token': access_token
            }
        }), 200
    except Exception as e:
        current_app.logger.error(f"Token refresh error: {str(e)}")
        return internal_server_error('Error refreshing token')

@bp.route('/auth/cleanup', methods=['POST'])
@jwt_required()
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

@bp.route('/auth/google/login')
def google_login():
    try:
        # Generate secure state
        state = secrets.token_urlsafe(32)
        current_app.logger.info(f"Generated CSRF State: {state[:10]}...")
        
        # Store state in session with prefix
        session['google_oauth_state'] = state
        session.modified = True  # Ensure session is saved
        
        # Create OAuth flow
        flow = GoogleAuthService.get_google_oauth_flow()
        
        # Generate authorization URL
        authorization_url, _ = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent",
            state=state
        )
        
        return redirect(authorization_url)
    except Exception as e:
        current_app.logger.error(f"Google OAuth login error: {str(e)}", exc_info=True)
        return internal_server_error('Failed to initiate Google OAuth login')

@bp.route('/auth/google/callback')
def google_callback():
    try:
        # Get states
        request_state = request.args.get('state')
        session_state = session.get('google_oauth_state')
        
        current_app.logger.info(f"Request State: {request_state[:10] if request_state else None}")
        current_app.logger.info(f"Session State: {session_state[:10] if session_state else None}")
        
        # Validate state
        if not request_state or not session_state:
            current_app.logger.error('Missing OAuth state')
            session.pop('google_oauth_state', None)  # Clean up
            return bad_request_error('Invalid OAuth state: State not found')
            
        if request_state != session_state:
            current_app.logger.error('State mismatch')
            session.pop('google_oauth_state', None)  # Clean up
            return bad_request_error('Invalid OAuth state: State mismatch')
            
        # Clean up state
        session.pop('google_oauth_state', None)
        session.modified = True
        
        # Log detailed callback information
        current_app.logger.info("Google OAuth Callback Received")
        current_app.logger.info(f"Full Request URL: {request.url}")
        current_app.logger.info(f"Request Arguments: {request.args}")
        
        # Check for authorization code
        authorization_code = request.args.get('code')
        if not authorization_code:
            current_app.logger.warning('No authorization code in callback')
            return bad_request_error('No authorization code received')
        
        # Create OAuth flow
        flow = GoogleAuthService.get_google_oauth_flow()
        
        try:
            # Fetch token with detailed logging
            current_app.logger.info("Attempting to fetch OAuth token")
            flow.fetch_token(authorization_response=request.url)
        except Exception as token_error:
            current_app.logger.error(f"Token fetching error: {str(token_error)}", exc_info=True)
            return internal_server_error(f'OAuth token retrieval failed: {str(token_error)}')
        
        # Fetch credentials
        credentials = flow.credentials
        
        # Get user info
        try:
            user_info = GoogleAuthService.get_google_user_info(credentials.token)
            current_app.logger.info(f"Retrieved user info for email: {user_info.get('email', 'Unknown')}")
        except Exception as user_info_error:
            current_app.logger.error(f"User info retrieval error: {str(user_info_error)}", exc_info=True)
            return internal_server_error('Failed to retrieve user information')
        
        # Validate and create/link user
        try:
            user = User.create_or_link_google_user(
                email=user_info['email'],
                name=user_info['name'],
                google_id=user_info['google_id'],
                picture=user_info.get('picture'),
                google_token=credentials.token
            )
            current_app.logger.info(f"User processed: {user.email}")
        except Exception as user_creation_error:
            current_app.logger.error(f"User creation/linking error: {str(user_creation_error)}", exc_info=True)
            return internal_server_error('Failed to process user account')
        
        # Generate tokens
        try:
            access_token = create_access_token(
                identity=user.id,
                additional_claims={
                    'email': user.email,
                    'roles': [role.name for role in user.roles]
                }
            )
            refresh_token = create_refresh_token(
                identity=user.id,
                additional_claims={
                    'email': user.email,
                    'roles': [role.name for role in user.roles]
                }
            )
        except Exception as token_generation_error:
            current_app.logger.error(f"Token generation error: {str(token_generation_error)}", exc_info=True)
            return internal_server_error('Failed to generate authentication tokens')
        
        current_app.logger.info("Google OAuth callback successful")
        return jsonify({
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': {
                'id': user.id,
                'email': user.email,
                'name': user.name,
                'picture': user.google_profile_pic
            }
        }), 200
    
    except ValueError as e:
        current_app.logger.warning(f"Google OAuth callback value error: {str(e)}")
        return bad_request_error(str(e))
    except Exception as e:
        current_app.logger.error(f"Unexpected Google OAuth callback error: {str(e)}", exc_info=True)
        return internal_server_error('Unexpected error during Google OAuth callback')
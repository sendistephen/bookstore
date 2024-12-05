from datetime import datetime, timedelta
from flask import current_app
import jwt
from app.models.user import User, db
from app.models.role import Role
from app.services.email_service import send_verification_email, send_password_reset_email
from app.services.role_service import RoleService
from utils.error_handler import bad_request_error

class AuthService:
    @staticmethod
    def register_user(data):
        """
        Register a new user and send verification email
        """
        try:
            # Check if user exists (case-insensitive)
            existing_username = User.query.filter(
                db.func.lower(User.username) == db.func.lower(data['username'])
            ).first()
            if existing_username:
                raise ValueError('Username already exists')

            existing_email = User.query.filter(
                db.func.lower(User.email) == db.func.lower(data['email'])
            ).first()
            if existing_email:
                raise ValueError('Email already exists')
            
            # Validate password
            is_valid, message = User.validate_password(data['password'])
            if not is_valid:
                raise ValueError(message)
            
            # Create user
            user = User(
                username=data['username'],
                name=data['name'],
                email=data['email'],
                phone=data.get('phone')
            )
            user.set_password(data['password'])
            
            # Generate verification token and save user
            db.session.add(user)
            db.session.flush()  # Get the user ID
            
            verification_token = user.generate_verification_token()
            
            # Get or create customer role and assign to user
            customer_role = RoleService.get_customer_role()
            if not customer_role:
                raise ValueError('Failed to create customer role')
            user.roles.append(customer_role)
            
            db.session.commit()
            
            # Send verification email
            verification_url = f"{current_app.config['API_HOST']}/api/v1/auth/verify-email/{verification_token}"
            send_verification_email(user, verification_url)
            
            return user
            
        except ValueError as e:
            db.session.rollback()
            raise ValueError(str(e))
        except Exception as e:
            db.session.rollback()
            raise Exception(f'Error during registration: {str(e)}')

    @staticmethod
    def login_user(email, password):
        """
        Authenticate user and generate access token
        """
        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            raise ValueError('Invalid email or password')
            
        if not user.is_verified:
            raise ValueError('Please verify your email before logging in')
            
        if not user.is_active:
            raise ValueError('Your account has been deactivated')
            
        # Generate access token
        access_token = AuthService.generate_access_token(user)
        
        return {
            'access_token': access_token,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'name': user.name,
                'roles': [role.name for role in user.roles]
            }
        }

    @staticmethod
    def generate_token(user, token_type='access', expiration=None):
        """
        Generate JWT token for user
        
        Args:
            user (User): User object
            token_type (str): Type of token (access or refresh)
            expiration (int, optional): Token expiration time in minutes
        
        Returns:
            str: JWT token
        """
        try:
            # Use configuration-based expiration if not specified
            if expiration is None:
                if token_type == 'access':
                    expiration = int(current_app.config.get('JWT_ACCESS_TOKEN_EXPIRES', timedelta(days=30)).total_seconds() / 60)
                elif token_type == 'refresh':
                    expiration = int(current_app.config.get('JWT_REFRESH_TOKEN_EXPIRES', timedelta(days=7)).total_seconds() / 60)
                else:
                    expiration = 30  # default fallback
            
            # Payload data
            payload = {
                'user_id': user.id,
                'email': user.email,
                'roles': [role.name for role in user.roles],
                'token_type': token_type,
                'exp': datetime.utcnow() + timedelta(minutes=expiration),
                'iat': datetime.utcnow()
            }
            
            # Use different secrets for different token types
            secret_key = current_app.config.get(
                'JWT_SECRET_KEY' if token_type == 'refresh' else 'SECRET_KEY'
            )
            
            # Generate the token
            token = jwt.encode(
                payload, 
                secret_key, 
                algorithm='HS256'
            )
            
            return token
        
        except Exception as e:
            current_app.logger.error(f"Error generating token: {str(e)}")
            raise

    @staticmethod
    def generate_access_token(user):
        """
        Generate access token
        
        Args:
            user (User): User object
        
        Returns:
            str: Access token
        """
        return AuthService.generate_token(user, token_type='access')

    @staticmethod
    def generate_refresh_token(user):
        """
        Generate refresh token
        
        Args:
            user (User): User object
        
        Returns:
            str: Refresh token
        """
        return AuthService.generate_token(user, token_type='refresh')

    @staticmethod
    def validate_token(token, token_type='access'):
        """
        Validate JWT token
        
        Args:
            token (str): JWT token
            token_type (str): Type of token to validate
        
        Returns:
            dict: Decoded token payload
        """
        try:
            # Select appropriate secret key based on token type
            secret_key = {
                'access': current_app.config.get('SECRET_KEY'),
                'refresh': current_app.config.get('JWT_SECRET_KEY')
            }.get(token_type, current_app.config.get('SECRET_KEY'))
            
            # Decode and validate token
            payload = jwt.decode(token, secret_key, algorithms=['HS256'])
            
            # Additional token type validation
            if payload.get('token_type') != token_type:
                raise jwt.InvalidTokenError("Invalid token type")
            
            return payload
        
        except jwt.ExpiredSignatureError:
            raise ValueError("Token has expired")
        except jwt.InvalidTokenError as e:
            raise ValueError(f"Invalid token: {str(e)}")
        except Exception as e:
            current_app.logger.error(f"Token validation error: {str(e)}")
            raise ValueError("Token validation failed")

    @staticmethod
    def verify_token(token):
        """
        Verify JWT token and return user
        
        Args:
            token (str): JWT token
        
        Returns:
            User: User object
        """
        try:
            payload = AuthService.validate_token(token)
            user = User.query.get(payload['user_id'])
            if not user:
                raise ValueError('User not found')
            return user
        except jwt.ExpiredSignatureError:
            raise ValueError('Token has expired')
        except jwt.InvalidTokenError:
            raise ValueError('Invalid token')

    @staticmethod
    def verify_email(token):
        """
        Verify user's email with token
        
        Args:
            token (str): Verification token
        
        Returns:
            User: User object
        """
        try:
            # Find user with this verification token
            user = User.query.filter_by(verification_token=token).first()
            if not user:
                raise ValueError('Invalid verification token')
                
            # Verify the token
            if not user.verify_email(token):
                raise ValueError('Invalid or expired verification token')
                
            return user
                
        except Exception as e:
            raise ValueError(f'Error verifying email: {str(e)}')

    @staticmethod
    def initiate_password_reset(email):
        """
        Generate password reset token and send email

        Args:
            email (str): User's email

        Returns:
            bool: True if email sent successfully
        """
        user = User.query.filter_by(email=email).first()
        if not user:
            # Don't reveal if email exists
            return True
            
        token = user.generate_reset_token()
        reset_url = f"{current_app.config['API_HOST']}/api/v1/auth/reset-password/{token}"
        
        try:
            send_password_reset_email(user, reset_url)
            return True
        except Exception as e:
            current_app.logger.error(f"Error sending reset email: {str(e)}")
            raise Exception('Error sending password reset email')

    @staticmethod
    def reset_password(token, new_password):
        """
        Reset user's password using reset token

        Args:
            token (str): Reset token
            new_password (str): New password

        Returns:
            bool: True if password reset successful
        """
        user = User.query.filter_by(reset_token=token).first()
        if not user or not user.verify_reset_token(token):
            raise ValueError('Invalid or expired reset token')
            
        if not User.validate_password(new_password):
            raise ValueError('Password does not meet requirements')
            
        user.set_password(new_password)
        user.reset_token = None
        user.reset_token_expires = None
        
        db.session.commit()
        return True

    @staticmethod
    def change_password(user_id, current_password, new_password):
        """
        Change user's password

        Args:
            user_id (int): User's ID
            current_password (str): Current password
            new_password (str): New password

        Returns:
            bool: True if password changed successfully
        """
        user = User.query.get(user_id)
        if not user:
            raise ValueError('User not found')
            
        if not user.check_password(current_password):
            raise ValueError('Current password is incorrect')
            
        if not User.validate_password(new_password):
            raise ValueError('New password does not meet requirements')
            
        user.set_password(new_password)
        db.session.commit()
        return True

    @staticmethod
    def delete_user_by_email(email):
        """Delete a user by email"
        
        Args:
            email (str): User's email
        
        Returns:
            bool: True if user deleted successfully
        """
        try:
            user = User.query.filter(
                db.func.lower(User.email) == db.func.lower(email)
            ).first()
            if user:
                db.session.delete(user)
                db.session.commit()
                return True
            return False
        except Exception as e:
            db.session.rollback()
            raise Exception(f'Error deleting user: {str(e)}')

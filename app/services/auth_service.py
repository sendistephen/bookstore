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
        access_token = AuthService.generate_token(user)
        
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
    def generate_token(user):
        """
        Generate JWT token for user
        """
        payload = {
            'user_id': user.id,
            'exp': datetime.utcnow() + current_app.config['JWT_ACCESS_TOKEN_EXPIRES'],
            'iat': datetime.utcnow(),
            'roles': [role.name for role in user.roles]
        }
        return jwt.encode(
            payload,
            current_app.config['JWT_SECRET_KEY'],
            algorithm='HS256'
        )

    @staticmethod
    def verify_token(token):
        """
        Verify JWT token and return user
        """
        try:
            payload = jwt.decode(
                token,
                current_app.config['JWT_SECRET_KEY'],
                algorithms=['HS256']
            )
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
        """Delete a user by email"""
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

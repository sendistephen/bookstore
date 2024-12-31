from marshmallow import fields, Schema, validate, validates
from app.models.user import User
from utils.error_handler import bad_request_error
from app.extensions import ma

class UserSchema(ma.SQLAlchemyAutoSchema):
    """Schema for serializing user data"""
    class Meta:
        model = User
        load_instance = True
        exclude = ('password_hash',)

class UserRegistrationSchema(Schema):
    """Schema for user registration validation"""
    username = fields.Str(
        required=True,
        validate=[
            validate.Length(
                min=2, max=32, error="Username must be between 2 and 32 characters"),
            validate.Regexp(
                regex=r'^[a-zA-Z0-9_]+$',
                error='Username must contain only letters, numbers, and underscores'
            )
        ],
        metadata={'error': 'Username is required'}
    )
    name = fields.Str(
        required=True,
        validate=validate.Length(
            min=2,
            max=32,
            error="Name must be between 2 and 32 characters"),
        metadata={'error': 'Name is required'}
    )
    email = fields.Email(required=True)
    phone = fields.Str(required=False, allow_none=True, validate=validate.Regexp(
        regex=r'^\+(?:[0-9]){6,14}[0-9]$',
        error='Phone number must be in the international format, starting with + and containing 7 to 15 digits'
    ))
    password = fields.Str(
        required=True,
        validate=[
            validate.Length(
                min=8,
                error="Password must be at least 8 characters long"
            )
        ],
        metadata={'error': 'Password is required'}
    )

    @validates('email')
    def validate_email(self, value):
        """Email validation"""
        # check if email already exists
        if User.query.filter_by(email=value).first():
            raise validate.ValidationError('Email already exists')
        return value

    @validates('username')
    def validate_username(self, value):
        """Username validation"""
        # check if username already exists
        if User.query.filter_by(username=value).first():
            raise validate.ValidationError('Username already exists')
        return value


class UserLoginSchema(Schema):
    """Schema for user login validation"""
    email = fields.Email(
        required=True,
        error_messages={'required': 'Email is required'}
    )
    password = fields.Str(
        required=True,
        error_messages={'required': 'Password is required'}
    )


class PasswordResetRequestSchema(Schema):
    """Schema for password reset request validation"""
    email = fields.Email(
        required=True,
        error_messages={'required': 'Email is required'}
    )


class PasswordResetSchema(Schema):
    """Schema for password reset validation"""
    new_password = fields.Str(
        required=True,
        validate=[
            validate.Length(
                min=8,
                error="Password must be at least 8 characters long"
            )
        ],
        error_messages={'required': 'New password is required'}
    )


class PasswordChangeSchema(Schema):
    """Schema for password change validation"""
    current_password = fields.Str(
        required=True,
        error_messages={'required': 'Current password is required'}
    )
    new_password = fields.Str(
        required=True,
        validate=[
            validate.Length(
                min=8,
                error="Password must be at least 8 characters long"
            )
        ],
        error_messages={'required': 'New password is required'}
    )
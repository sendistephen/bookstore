import os
import logging
import json
import pathlib
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from flask import current_app
from string import Template
from utils.error_handler import (
    bad_request_error, 
    internal_server_error, 
    unauthorized_error
)

# Monkey patch to allow insecure transport
import oauthlib.oauth2.rfc6749.parameters as oauth_params
oauth_params.VALIDATE_TRANSPORT = False

class GoogleAuthService:
    """Google authentication service"""
    
    @staticmethod
    def _load_client_secrets():
        """
        Load and substitute client secrets with environment variables
        
        Returns:
            dict: Processed client secrets
        """
        try:
            # Extensive logging for debugging
            logging.info("Starting client secrets loading process")
            logging.info(f"Current environment variables:")
            for key, value in os.environ.items():
                if key.startswith('GOOGLE_'):
                    logging.info(f"  {key}: {'*' * len(value) if value else 'EMPTY'}")
            
            # Path to client secrets file
            client_secrets_path = os.path.join(
                pathlib.Path(__file__).parent.parent.parent, 
                'client_secret.json'
            )
            logging.info(f"Client secrets path: {client_secrets_path}")
            
            # Read the file
            with open(client_secrets_path, 'r') as f:
                secrets_template = Template(f.read())
            
            # Substitute environment variables
            secrets_str = secrets_template.safe_substitute(os.environ)
            logging.info("Environment variable substitution completed")
            
            # Parse the JSON
            secrets = json.loads(secrets_str)
            
            # Validate the required fields with extensive logging
            required_fields = ['client_id', 'client_secret', 'redirect_uris']
            for field in required_fields:
                value = secrets['web'].get(field)
                if not value:
                    error_msg = f"Missing required Google OAuth field: {field}"
                    logging.error(error_msg)
                    raise ValueError(error_msg)
                
                # Mask sensitive information in logs
                masked_value = value[0] if isinstance(value, list) else value
                masked_value = masked_value[:4] + '*' * (len(masked_value) - 8) + masked_value[-4:] if len(masked_value) > 8 else masked_value
                logging.info(f"Loaded {field}: {masked_value}")
            
            return secrets
        except FileNotFoundError:
            logging.error("Client secrets file not found")
            raise bad_request_error("Google OAuth configuration is missing")
        except json.JSONDecodeError:
            logging.error("Invalid JSON in client secrets file")
            raise internal_server_error("Invalid Google OAuth configuration")
        except Exception as e:
            logging.error(f"Comprehensive error loading client secrets: {str(e)}", exc_info=True)
            raise internal_server_error(f"Error loading Google OAuth configuration: {str(e)}")

    @staticmethod
    def get_google_oauth_flow(scopes=None):
        """
        Initialize and return Google OAuth flow
        
        Returns:
            Flow: Configured Google OAuth flow
        """
        if scopes is None:
            scopes = [
                'openid', 
                'https://www.googleapis.com/auth/userinfo.email', 
                'https://www.googleapis.com/auth/userinfo.profile'
            ]
        
        try:
            # Allow insecure transport for development
            os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
            
            # Log scopes
            logging.info(f"OAuth Scopes: {scopes}")
            
            # Validate required environment variables
            client_id = os.getenv('GOOGLE_CLIENT_ID')
            client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
            redirect_uri = os.getenv(
                'GOOGLE_REDIRECT_URI', 
                'http://localhost:8080/api/v1/auth/google/callback'
            )
            
            if not client_id or not client_secret:
                logging.error("Missing Google OAuth credentials")
                raise unauthorized_error("Google OAuth credentials are not configured")
            
            # Use the root directory of the project
            client_secrets = GoogleAuthService._load_client_secrets()
            
            # Create a flow directly from loaded client secrets
            flow = Flow.from_client_config(
                client_secrets,
                scopes=scopes
            )
            
            # Extensive logging for redirect URI
            logging.info(f"Environment GOOGLE_REDIRECT_URI: {redirect_uri}")
            
            flow.redirect_uri = redirect_uri
            
            return flow
        
        except Exception as e:
            logging.error(f'Comprehensive Google OAuth flow initialization error: {str(e)}', exc_info=True)
            raise internal_server_error(f'Error initializing Google OAuth flow: {str(e)}')

    @staticmethod
    def validate_google_token(token):
        """
        Validate Google ID token
        
        Args:
            token (str): Google ID token

        Returns:
            dict: Google user information
        """
        
        try:
            # Verify the token
            id_info = id_token.verify_oauth2_token(token, google.auth.transport.Request(),
            os.getenv('GOOGLE_CLIENT_ID'))
            
            # Validate issuer
            if id_info['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                raise ValueError('Invalid issuer')
            
            return {
                'email': id_info.get('email'),
                'name': id_info.get('name'),
                'picture': id_info.get('picture'),
                'google_id': id_info.get('sub')
                }
            
        except ValueError as e:
            logging.error(f'Google token validation error: {str(e)}')
            return bad_request_error('Invalid google token')

    
    @staticmethod
    def get_google_user_info(access_token):
        """
        Retrieve user information from Google
        
        Args:
            access_token (str): OAuth access token
        
        Returns:
            Dict of user information
        """
        try:
            credentials = Credentials(token=access_token)
            service = build('oauth2', 'v2', credentials=credentials)
            user_info = service.userinfo().get().execute()
            
            return {
                'google_id': user_info['id'],
                'email': user_info['email'],
                'name': user_info.get('name'),
                'picture': user_info.get('picture')
            }
        except Exception as e:
            logging.error(f"Error fetching Google user info: {str(e)}")
            raise ValueError("Failed to retrieve user information from Google")
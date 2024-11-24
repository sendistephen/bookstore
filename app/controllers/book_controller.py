from flask import Blueprint
from app.blueprints.api_v1 import api_v1_bp

# health check


@api_v1_bp.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return f'App is healthy', 200

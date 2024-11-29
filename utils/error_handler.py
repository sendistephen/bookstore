from werkzeug.http import HTTP_STATUS_CODES
from flask import jsonify
from datetime import datetime


def error_response(status_code, message=None):
    """Generate an error response"""
    payload = {
        "status": "fail" if status_code < 500 else "error",
        "data": {"message": HTTP_STATUS_CODES.get(status_code, "unknown error") if not message else message},
        "timestamp": datetime.utcnow().isoformat()
    }

    response = jsonify(payload)
    response.status_code = status_code
    return response


def not_found(message=None):
    """Generate a 404 not found error response"""
    payload = {
        "status": "fail",
        "data": {"message": message or "Resource not found"},
        "timestamp": datetime.utcnow().isoformat()
    }
    response = jsonify(payload)
    response.status_code = 404
    return response


def bad_request_error(message=None):
    """Generate a 400 bad request error response"""
    payload = {
        "status": "fail",
        "data": message if isinstance(message, dict) else {"message": message},
        "timestamp": datetime.utcnow().isoformat()
    }
    response = jsonify(payload)
    response.status_code = 400
    return response


def unauthorized_error(message=None):
    """Generate a 401 unauthorized error response"""
    payload = {
        "status": "fail",
        "data": {"message": message or "Unauthorized access"},
        "timestamp": datetime.utcnow().isoformat()
    }
    response = jsonify(payload)
    response.status_code = 401
    return response


def forbidden_error(message=None):
    """Generate a 403 forbidden error response"""
    payload = {
        "status": "fail",
        "data": {"message": message or "Forbidden access"},
        "timestamp": datetime.utcnow().isoformat()
    }
    response = jsonify(payload)
    response.status_code = 403
    return response


def internal_server_error(message=None):
    """Generate a 500 internal server error response"""
    payload = {
        "status": "error",
        "data": {"message": message or "Internal server error"},
        "timestamp": datetime.utcnow().isoformat()
    }
    response = jsonify(payload)
    response.status_code = 500
    return response

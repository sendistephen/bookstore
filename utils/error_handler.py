from werkzeug.http import HTTP_STATUS_CODES
from flask import jsonify
from datetime import datetime


def error_response(status_code, message=None):
    """Generate an error response
    
    :param status_code: HTTP status code
    :param message: Error message
    :return: JSON response
    """
    payload = {
        "status": "error" if status_code >= 500 else "fail",
        "data": {"message": HTTP_STATUS_CODES.get(status_code, "unknown error") if not message else message},
        "timestamp": datetime.utcnow().isoformat()
    }

    response = jsonify(payload)
    response.status_code = status_code
    return response


def not_found(message=None):
    """Generate a 404 not found error response"""
    return error_response(404, message or "Resource not found")


def bad_request_error(message=None):
    """Generate a 400 bad request error response"""
    return error_response(400, message or "Bad request")


def unauthorized_error(message=None):
    """Generate a 401 unauthorized error response"""
    return error_response(401, message or "Unauthorized access")


def forbidden_error(message=None):
    """Generate a 403 forbidden error response"""
    return error_response(403, message or "Forbidden access")


def internal_server_error(message=None):
    """Generate a 500 internal server error response"""
    return error_response(500, message or "Internal server error")


def method_not_allowed_error(message=None):
    """Generate a 405 method not allowed error response"""
    return error_response(405, message or "Method not allowed")


def conflict_error(message=None):
    """Generate a 409 conflict error response"""
    return error_response(409, message or "Conflict")


def gateway_timeout_error(message=None):
    """Generate a 504 gateway timeout error response"""
    return error_response(504, message or "Gateway timeout")

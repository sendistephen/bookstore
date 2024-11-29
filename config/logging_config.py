import os
import logging
import json
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from datetime import datetime
from typing import Dict, Any

def json_log_formatter(record: logging.LogRecord) -> str:
    """
    Create a JSON-formatted log record.
    
    Args:
        record (logging.LogRecord): The log record to format.
    
    Returns:
        str: A JSON-formatted log message.
    """
    log_record: Dict[str, Any] = {
        'timestamp': datetime.utcnow().isoformat(),
        'level': record.levelname,
        'logger': record.name,
        'message': record.getMessage(),
        'module': record.module,
        'func_name': record.funcName,
        'line_no': record.lineno,
    }
    
    # Add exception information if present
    if record.exc_info:
        log_record['exception'] = {
            'type': str(record.exc_info[0]),
            'message': str(record.exc_info[1]),
        }
    
    return json.dumps(log_record)

class JSONFormatter(logging.Formatter):
    """
    A custom JSON log formatter for structured logging.
    """
    def format(self, record: logging.LogRecord) -> str:
        return json_log_formatter(record)

def create_rotating_file_handler(
    filename: str, 
    level: int = logging.INFO, 
    max_bytes: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 5
) -> RotatingFileHandler:
    """
    Create a rotating file handler with JSON formatting.
    
    Args:
        filename (str): Name of the log file.
        level (int): Logging level.
        max_bytes (int): Maximum log file size before rotation.
        backup_count (int): Number of backup log files to keep.
    
    Returns:
        RotatingFileHandler: Configured log handler.
    """
    # Ensure logs directory exists
    os.makedirs('logs', exist_ok=True)
    
    full_path = os.path.join('logs', filename)
    handler = RotatingFileHandler(
        full_path, 
        maxBytes=max_bytes, 
        backupCount=backup_count
    )
    handler.setFormatter(JSONFormatter())
    handler.setLevel(level)
    return handler

def setup_logging(app):
    """
    Configure comprehensive logging for the Flask application.
    
    Args:
        app (Flask): The Flask application instance.
    """
    # Logging configuration
    log_level = logging.INFO if not app.debug else logging.DEBUG
    
    # Create handlers
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(JSONFormatter())
    console_handler.setLevel(log_level)
    
    # File handlers
    app.logger.addHandler(console_handler)
    app.logger.addHandler(create_rotating_file_handler('application.log', level=log_level))
    app.logger.addHandler(create_rotating_file_handler('error.log', level=logging.ERROR))
    
    # Set overall logging level
    app.logger.setLevel(log_level)
    
    # Configure Werkzeug logger
    werkzeug_logger = logging.getLogger('werkzeug')
    werkzeug_logger.setLevel(log_level)
    werkzeug_logger.addHandler(console_handler)
    
    # Log application startup
    app.logger.info('Bookstore application logging initialized')

def log_exception(e: Exception, logger: logging.Logger = None):
    """
    Utility function to log exceptions with additional context.
    
    Args:
        e (Exception): The exception to log.
        logger (logging.Logger, optional): Logger to use. Defaults to root logger.
    """
    if logger is None:
        logger = logging.getLogger(__name__)
    
    logger.exception(f"Unhandled exception: {str(e)}", exc_info=True)

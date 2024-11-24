import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime


def setup_logging(app):
    if not app.debug:
        # Ensure the logs directory exists
        os.makedirs('logs', exist_ok=True)

        # combined log handler
        combined_handler = RotatingFileHandler(
            f'logs/combined-{datetime.now().strftime("%Y-%m-%d-%H")}.log', maxBytes=1024, backupCount=10
        )
        combined_handler.setFormatter(logging.Formatter(
            '{"message": "%(message)s", "level": "%(levelname)s", "timestamp": "%(asctime)s"}'
        ))
        combined_handler.setLevel(logging.DEBUG)
        app.logger.addHandler(combined_handler)

        # error log handler
        error_handler = RotatingFileHandler(
            f'logs/error.log', maxBytes=1024, backupCount=10
        )
        error_handler.setFormatter(logging.Formatter(
            '{"message": "%(message)s", "level": "%(levelname)s", "timestamp": "%(asctime)s"}'
        ))
        error_handler.setLevel(logging.ERROR)
        app.logger.addHandler(error_handler)

        # Exception log handler
        exception_handler = RotatingFileHandler(
            f'logs/exception.log', maxBytes=1024, backupCount=10
        )
        exception_handler.setFormatter(logging.Formatter(
            '{"message": "%(message)s", "level": "%(levelname)s", "timestamp": "%(asctime)s"}'
        ))
        exception_handler.setLevel(logging.ERROR)
        app.logger.addHandler(exception_handler)

        # Rejection log handler
        rejection_handler = RotatingFileHandler(
            f'logs/rejection.log', maxBytes=1024, backupCount=10
        )
        rejection_handler.setFormatter(logging.Formatter(
            '{"message": "%(message)s", "level": "%(levelname)s", "timestamp": "%(asctime)s"}'
        ))
        rejection_handler.setLevel(logging.ERROR)
        app.logger.addHandler(rejection_handler)

        # set the logging level
        app.logger.setLevel(logging.INFO)
        app.logger.info('Bookstore startup')

        # Configure werkzeug logger to use the same handlers
        werkzeug_logger = logging.getLogger('werkzeug')
        werkzeug_logger.setLevel(logging.INFO)
        werkzeug_logger.addHandler(combined_handler)

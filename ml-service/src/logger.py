"""
Production-grade logging system
- JSON structured logs for ELK/Splunk integration
- Rotating file handlers to prevent disk bloat
- Console output for development
- Single logger instance for app-wide use
"""

import json
import logging
import logging.handlers
from datetime import datetime

from config.settings import config
from pythonjsonlogger import jsonlogger


class ProductionLogger:
    """
    Enterprise logging setup

    Features:
    - Structured JSON logging for parsing
    - Rotating file handlers
    - Console output for development
    - Different formatters for file vs console
    """

    @staticmethod
    def setup():
        """
        Initialize and configure logging system

        Returns:
            logging.Logger instance ready for use
        """

        # Create logger
        logger = logging.getLogger('ml-service')
        logger.setLevel(config.LOGGING.LEVEL)

        # ============= FILE HANDLER (JSON) =============
        # Use rotating file handler to avoid huge log files
        file_handler = logging.handlers.RotatingFileHandler(
            config.LOGGING.FILE,
            maxBytes=config.LOGGING.MAX_BYTES,      # 10MB per file
            backupCount=config.LOGGING.BACKUP_COUNT  # Keep 5 files
        )

        # JSON formatter for structured logging
        # Format: {"timestamp": "2026-01-19T...", "name": "ml-service", "level": "INFO", "message": "..."}
        json_formatter = jsonlogger.JsonFormatter(
            '%(timestamp)s %(name)s %(levelname)s %(message)s',
            rename_fields={'timestamp': '@timestamp'}  # Compatible with ELK stack
        )
        file_handler.setFormatter(json_formatter)

        # ============= CONSOLE HANDLER (HUMAN-READABLE) =============
        # For development/debugging - easy to read
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter(config.LOGGING.FORMAT)
        console_handler.setFormatter(console_formatter)

        # ============= ADD HANDLERS =============
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        # Log startup message
        logger.info(
            f"Logging initialized | "
            f"Level: {config.LOGGING.LEVEL} | "
            f"File: {config.LOGGING.FILE}"
        )

        return logger

# Initialize logger on module import
# This runs when you do: from src.logger import logger
logger = ProductionLogger.setup()

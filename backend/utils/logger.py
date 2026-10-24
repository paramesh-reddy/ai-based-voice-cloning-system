"""
Logging utility for AI-Based Voice Cloning System.

Provides structured, privacy-conscious logging without recording
sensitive audio samples, transcripts, or private personal data.
"""

import logging
import os
import sys
from typing import Optional


def get_logger(name: str = "voice_cloning", level: Optional[str] = None) -> logging.Logger:
    """
    Configures and returns a logger instance with privacy-safe formatting.

    Args:
        name: Name of the logger component.
        level: Optional log level override (DEBUG, INFO, WARNING, ERROR).

    Returns:
        logging.Logger: Configured logger instance.
    """
    logger = logging.getLogger(name)

    # Avoid duplicate handlers if already configured
    if logger.handlers:
        return logger

    log_level_name = level or os.getenv("LOG_LEVEL", "INFO").upper()
    numeric_level = getattr(logging, log_level_name, logging.INFO)
    logger.setLevel(numeric_level)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(numeric_level)

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.propagate = False

    return logger

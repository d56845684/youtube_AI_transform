import logging
import os
from typing import Optional

_LOG_LEVEL = os.getenv("APP_LOG_LEVEL", "INFO").upper()
_LOG_FORMAT = "%(asctime)s %(levelname)s [%(name)s] %(message)s"

logging.basicConfig(level=_LOG_LEVEL, format=_LOG_FORMAT)


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Return a logger with unified formatting and level configuration."""

    return logging.getLogger(name or "app")

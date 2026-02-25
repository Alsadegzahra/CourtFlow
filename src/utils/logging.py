"""
Consistent logger setup.
"""
from __future__ import annotations

import logging
import sys

from src.config.settings import LOG_LEVEL


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        h = logging.StreamHandler(sys.stdout)
        h.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
        logger.addHandler(h)
        logger.setLevel(getattr(logging, LOG_LEVEL.upper(), logging.INFO))
    return logger

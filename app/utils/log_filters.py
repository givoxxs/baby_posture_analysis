"""Custom logging filters."""

import logging
from app.config import settings


class RequireDebugFalse(logging.Filter):
    """Filter that only allows records when DEBUG is False."""
    
    def filter(self, record):
        """Return True if DEBUG setting is False."""
        return not settings.DEBUG


class RequireDebugTrue(logging.Filter):
    """Filter that only allows records when DEBUG is True."""
    
    def filter(self, record):
        """Return True if DEBUG setting is True."""
        return settings.DEBUG

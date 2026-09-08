"""Custom exception classes for the backend."""


class AppError(Exception):
    """Base application error."""


class ValidationError(AppError):
    """Raised when request validation fails."""


class NotFoundError(AppError):
    """Raised when a requested resource is missing."""

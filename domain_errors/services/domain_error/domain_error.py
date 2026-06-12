"""DomainError base class (Stage 1 single file)."""

from __future__ import annotations


class DomainError(Exception):
    """Base for per-project typed exception hierarchies."""

    code: str = "domain_error"
    http_status: int = 500
    retryable: bool = False
    default_message: str = "An unspecified domain error occurred."

    def __init__(self, message: str | None = None, **context: object) -> None:
        """Store the message and logger context, then initialize Exception."""
        self.message = message or self.default_message
        self.context = context
        super().__init__(self.message)

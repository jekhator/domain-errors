"""Domain error test fixtures."""

import pytest

from domain_errors.domains.domain_error.domain_error import DomainError


class CustomDomainError(DomainError):
    """A custom DomainError subclass with overridden classvars."""

    code = "CUSTOM_CODE"
    domain = "custom_domain"
    http_status = 403
    retryable = True
    default_message = "Custom domain error."


@pytest.fixture
def custom_error_class() -> type[CustomDomainError]:
    """Provide a custom DomainError subclass for testing."""
    return CustomDomainError

"""Tests for ErrorChain domain resolution (_domain_of)."""

from domain_errors.domains.domain_error.domain_error import DomainError
from domain_errors.services.chain.chain_client import ErrorChain
from domain_errors.services.tests.test_chain.conftest import FakeDomainClassifier


class CustomDomainError(DomainError):
    """A custom domain error for testing."""

    code = "CUSTOM"
    domain = "custom"
    http_status = 400
    retryable = True
    default_message = "Custom error occurred."


class TestErrorChainDomainOf:
    """Tests for ErrorChain._domain_of()."""

    def test_domain_from_classvar(self) -> None:
        """_domain_of returns the domain classvar if it is a string."""
        err = CustomDomainError()
        domain = ErrorChain._domain_of(err, classifiers=())
        assert domain == "custom"

    def test_domain_from_first_matching_classifier(self) -> None:
        """_domain_of uses the first classifier that returns non-None."""
        classifier = FakeDomainClassifier()
        err = ValueError("test")
        domain = ErrorChain._domain_of(err, classifiers=(classifier,))
        assert domain == "validation"

    def test_domain_fallback_python(self) -> None:
        """_domain_of defaults to 'python' when no classifier matches."""
        classifier = FakeDomainClassifier()
        err = KeyError("test")
        domain = ErrorChain._domain_of(err, classifiers=(classifier,))
        assert domain == "python"

    def test_domain_ignores_non_string_attribute(self) -> None:
        """_domain_of ignores a domain attribute that is not a string."""
        err = ValueError("test")
        err.domain = 123  # type: ignore
        classifier = FakeDomainClassifier()
        domain = ErrorChain._domain_of(err, classifiers=(classifier,))
        assert domain == "validation"

"""Chain test fixtures."""

import pytest


class FakeDomainClassifier:
    """Concrete classifier that recognizes fake test exceptions."""

    def classify(self, err: BaseException) -> str | None:
        """Return a domain for test exceptions, or None for unrecognized errors."""
        if isinstance(err, ValueError):
            return "validation"
        if isinstance(err, TypeError):
            return "typing"
        return None


@pytest.fixture
def fake_classifier() -> FakeDomainClassifier:
    """Provide a concrete classifier for testing."""
    return FakeDomainClassifier()

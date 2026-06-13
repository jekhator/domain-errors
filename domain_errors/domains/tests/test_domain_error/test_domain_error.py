"""Tests for DomainError base class."""

import pytest

from domain_errors.domains.domain_error.domain_error import DomainError
from domain_errors.domains.tests.test_domain_error.conftest import CustomDomainError


class TestDomainErrorConstruction:
    """Tests for DomainError initialization."""

    def test_construction_with_message(self) -> None:
        """DomainError can be constructed with a message."""
        err = DomainError(message="custom message")
        assert err.message == "custom message"

    def test_construction_with_none_message_uses_default(self) -> None:
        """DomainError with message=None uses default_message."""
        err = DomainError(message=None)
        assert err.message == DomainError.default_message

    def test_construction_without_message_arg_uses_default(self) -> None:
        """DomainError without message arg uses default_message."""
        err = DomainError()
        assert err.message == DomainError.default_message

    def test_construction_stores_context_kwargs(self) -> None:
        """DomainError stores context kwargs in self.context dict."""
        err = DomainError(message="msg", user_id=42, request_id="abc")
        assert err.context == {"user_id": 42, "request_id": "abc"}

    def test_construction_empty_context(self) -> None:
        """DomainError with no context kwargs has an empty context dict."""
        err = DomainError(message="msg")
        assert err.context == {}

    def test_message_in_args(self) -> None:
        """DomainError stores message in Exception.args."""
        err = DomainError(message="test message")
        assert err.args[0] == "test message"

    def test_message_retrievable_via_str(self) -> None:
        """str(DomainError) returns the message."""
        err = DomainError(message="error text")
        assert str(err) == "error text"

    def test_custom_subclass_default_message(self) -> None:
        """DomainError subclass with custom default_message uses it."""
        err = CustomDomainError()
        assert err.message == "Custom domain error."

    def test_custom_subclass_message_override(self) -> None:
        """DomainError subclass with explicit message overrides default."""
        err = CustomDomainError(message="override")
        assert err.message == "override"

    def test_context_stored_in_instance_dict(self) -> None:
        """DomainError context and message are in __dict__, not __slots__."""
        err = DomainError(message="msg", key="value")
        assert "message" in err.__dict__
        assert "context" in err.__dict__
        assert err.__dict__["message"] == "msg"
        assert err.__dict__["context"] == {"key": "value"}


class TestDomainErrorClassVars:
    """Tests for DomainError classvars."""

    def test_base_code(self) -> None:
        """DomainError has a base code classvar."""
        assert DomainError.code == "domain_error"

    def test_base_domain(self) -> None:
        """DomainError has a base domain classvar."""
        assert DomainError.domain == "application"

    def test_base_http_status(self) -> None:
        """DomainError has a base http_status classvar."""
        assert DomainError.http_status == 500

    def test_base_retryable(self) -> None:
        """DomainError has a base retryable classvar."""
        assert DomainError.retryable is False

    def test_base_default_message(self) -> None:
        """DomainError has a base default_message classvar."""
        assert DomainError.default_message == "An unspecified domain error occurred."

    def test_subclass_code_override(self) -> None:
        """DomainError subclass can override code."""
        assert CustomDomainError.code == "CUSTOM_CODE"

    def test_subclass_domain_override(self) -> None:
        """DomainError subclass can override domain."""
        assert CustomDomainError.domain == "custom_domain"

    def test_subclass_http_status_override(self) -> None:
        """DomainError subclass can override http_status."""
        assert CustomDomainError.http_status == 403

    def test_subclass_retryable_override(self) -> None:
        """DomainError subclass can override retryable."""
        assert CustomDomainError.retryable is True

    def test_subclass_default_message_override(self) -> None:
        """DomainError subclass can override default_message."""
        assert CustomDomainError.default_message == "Custom domain error."

    def test_instance_retrieves_subclass_classvars(self) -> None:
        """DomainError instance has access to subclass classvars."""
        err = CustomDomainError()
        assert err.code == "CUSTOM_CODE"
        assert err.domain == "custom_domain"
        assert err.http_status == 403
        assert err.retryable is True


class TestDomainErrorChainingBehavior:
    """Tests for DomainError as an Exception."""

    def test_is_exception(self) -> None:
        """DomainError is an Exception subclass."""
        err = DomainError()
        assert isinstance(err, Exception)

    def test_can_be_raised(self) -> None:
        """DomainError can be raised and caught."""
        with pytest.raises(DomainError):
            raise DomainError(message="test")

    def test_can_be_raised_with_cause(self) -> None:
        """DomainError can be raised with a cause (from X)."""
        original = ValueError("original")
        try:
            raise DomainError(message="wrapped") from original
        except DomainError as e:
            assert e.__cause__ is original


class TestDomainErrorContextPropagation:
    """Tests for context propagation (known-behavior flag)."""

    def test_context_not_in_chain_links(self) -> None:
        """Current behavior: raise-site context does not propagate into the chain (pending design decision)."""
        # This test pins current behavior: context stored on DomainError
        # does NOT get extracted into ChainLink, because ChainLink has no
        # context field and to_log_extra() does not include context.
        from domain_errors.services.chain.chain_client import ErrorChain

        err = DomainError(message="error", user_id=42, request_id="xyz")
        assert err.context == {"user_id": 42, "request_id": "xyz"}
        links = ErrorChain.history(err)
        assert len(links) == 1
        extra = links[0].to_log_extra()
        # context is NOT in the link
        assert "user_id" not in extra
        assert "request_id" not in extra
        assert set(extra.keys()) == {"type", "message", "code", "domain", "via"}

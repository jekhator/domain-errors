"""Tests for ErrorChain client operations."""

from domain_errors.domains.domain_error.domain_error import DomainError
from domain_errors.services.chain.chain_client import ErrorChain
from domain_errors.services.chain.chain_objects import ChainVia
from domain_errors.services.tests.test_chain.conftest import FakeDomainClassifier


class CustomDomainError(DomainError):
    """A custom domain error for testing."""

    code = "CUSTOM"
    domain = "custom"
    http_status = 400
    retryable = True
    default_message = "Custom error occurred."


class TestErrorChainWrap:
    """Tests for ErrorChain.wrap()."""

    def test_wrap_returns_target_class(self) -> None:
        """wrap() returns an instance of the specified as_ class."""
        err = ValueError("oops")
        result = ErrorChain.wrap(err, as_=CustomDomainError)
        assert isinstance(result, CustomDomainError)

    def test_wrap_with_explicit_message(self) -> None:
        """wrap() uses the provided message."""
        err = ValueError("oops")
        result = ErrorChain.wrap(err, as_=CustomDomainError, message="custom msg")
        assert result.message == "custom msg"
        assert str(result) == "custom msg"

    def test_wrap_with_none_message_uses_default(self) -> None:
        """wrap() with message=None uses the class default_message."""
        err = ValueError("oops")
        result = ErrorChain.wrap(err, as_=CustomDomainError, message=None)
        assert result.message == CustomDomainError.default_message

    def test_wrap_with_no_message_arg_uses_default(self) -> None:
        """wrap() without message arg uses the class default_message."""
        err = ValueError("oops")
        result = ErrorChain.wrap(err, as_=CustomDomainError)
        assert result.message == CustomDomainError.default_message

    def test_wrap_stores_context_kwargs(self) -> None:
        """wrap() passes context kwargs to the domain error."""
        err = ValueError("oops")
        result = ErrorChain.wrap(
            err,
            as_=CustomDomainError,
            user_id=123,
            request_id="abc",
        )
        assert result.context["user_id"] == 123
        assert result.context["request_id"] == "abc"

    def test_wrap_intended_for_raise_from(self) -> None:
        """wrap() returns an object ready to be raised with 'from err'."""
        original = ValueError("bad")
        wrapped = ErrorChain.wrap(original, as_=CustomDomainError, message="wrapped")
        try:
            raise wrapped from original
        except CustomDomainError as e:
            assert e.__cause__ is original


class TestErrorChainHistory:
    """Tests for ErrorChain.history()."""

    def test_single_error_is_root(self) -> None:
        """history() of a single error returns one ROOT link."""
        err = ValueError("oops")
        classifier = FakeDomainClassifier()
        links = ErrorChain.history(err, classifiers=(classifier,))
        assert len(links) == 1
        assert links[0].type_name == "ValueError"
        assert links[0].message == "oops"
        assert links[0].via == ChainVia.ROOT
        assert links[0].domain == "validation"

    def test_explicit_cause_chain(self) -> None:
        """history() walks __cause__ chain, marking links as ROOT then CAUSE."""
        inner = ValueError("inner")
        outer = RuntimeError("outer")
        try:
            raise outer from inner
        except RuntimeError as e:
            links = ErrorChain.history(e)
        assert len(links) == 2
        assert links[0].type_name == "RuntimeError"
        assert links[0].via == ChainVia.ROOT
        assert links[1].type_name == "ValueError"
        assert links[1].via == ChainVia.CAUSE

    def test_implicit_context_chain(self) -> None:
        """history() walks __context__ chain when __suppress_context__ is False."""
        inner = ValueError("inner")
        outer = RuntimeError("outer")
        try:
            try:
                raise inner
            except ValueError:
                raise outer
        except RuntimeError as e:
            links = ErrorChain.history(e)
        assert len(links) == 2
        assert links[0].type_name == "RuntimeError"
        assert links[0].via == ChainVia.ROOT
        assert links[1].type_name == "ValueError"
        assert links[1].via == ChainVia.CONTEXT

    def test_suppress_context_stops_chain(self) -> None:
        """history() stops at __context__ when __suppress_context__ is True."""
        inner = ValueError("inner")
        outer = RuntimeError("outer")
        try:
            try:
                raise inner
            except ValueError:
                raise outer from None
        except RuntimeError as e:
            links = ErrorChain.history(e)
        # only outer, because "from None" suppresses context
        assert len(links) == 1
        assert links[0].type_name == "RuntimeError"

    def test_cycle_guard(self) -> None:
        """history() terminates on cycles and does not infinite loop."""
        # Manually create a cycle (raises on normal exception chaining)
        e1: BaseException = ValueError("e1")
        e2: BaseException = RuntimeError("e2")
        e1.__cause__ = e2
        e2.__cause__ = e1  # cycle
        links = ErrorChain.history(e1)
        # Should have exactly 2 links, then stop
        assert len(links) == 2
        assert links[0].type_name == "ValueError"
        assert links[1].type_name == "RuntimeError"

    def test_domain_resolution_from_classvar(self) -> None:
        """history() resolves domain from DomainError.domain classvar."""
        err = CustomDomainError()
        links = ErrorChain.history(err)
        assert links[0].domain == "custom"

    def test_domain_resolution_from_classifier(self) -> None:
        """history() uses the first matching classifier to resolve domain."""
        err = ValueError("test")
        classifier = FakeDomainClassifier()
        links = ErrorChain.history(err, classifiers=(classifier,))
        assert links[0].domain == "validation"

    def test_domain_resolution_classvar_takes_precedence(self) -> None:
        """history() prefers classvar domain over classifier."""
        err = CustomDomainError()
        classifier = FakeDomainClassifier()
        links = ErrorChain.history(err, classifiers=(classifier,))
        # CustomDomainError.domain = "custom", not "application"
        assert links[0].domain == "custom"

    def test_domain_fallback_to_python(self) -> None:
        """history() falls back to 'python' when no classifier matches."""
        err = KeyError("key")
        links = ErrorChain.history(err)
        assert links[0].domain == "python"

    def test_code_attribute_extracted(self) -> None:
        """history() extracts code attribute from DomainError."""
        err = CustomDomainError()
        links = ErrorChain.history(err)
        assert links[0].code == "CUSTOM"

    def test_code_none_when_absent(self) -> None:
        """history() sets code to None when error has no code attribute."""
        err = ValueError("test")
        links = ErrorChain.history(err)
        assert links[0].code is None

    def test_multiple_classifiers_first_match_wins(self) -> None:
        """history() uses the first classifier that returns non-None."""
        classifier1 = FakeDomainClassifier()
        classifier2 = FakeDomainClassifier()
        err = TypeError("test")
        links = ErrorChain.history(err, classifiers=(classifier1, classifier2))
        # Both would match TypeError, but classifier1 is first
        assert links[0].domain == "typing"


class TestErrorChainCrossings:
    """Tests for ErrorChain.crossings()."""

    def test_no_crossings_single_error(self) -> None:
        """crossings() returns empty tuple for a single error."""
        err = ValueError("oops")
        crossings = ErrorChain.crossings(err)
        assert crossings == ()

    def test_no_crossings_same_domain(self) -> None:
        """crossings() returns empty when all links have the same domain."""
        # Create a chain of errors that both resolve to the same domain
        err = KeyError("same domain")
        try:
            raise RuntimeError("also python domain") from err
        except RuntimeError as e:
            classifier = FakeDomainClassifier()
            crossings = ErrorChain.crossings(e, classifiers=(classifier,))
        # Both KeyError and RuntimeError unmatched, default to "python"
        assert len(crossings) == 0

    def test_crossing_on_domain_change(self) -> None:
        """crossings() returns DomainCrossing when adjacent links differ in domain."""
        inner = ValueError("validation failed")
        outer = RuntimeError("app failed")
        try:
            raise outer from inner
        except RuntimeError as e:
            classifier = FakeDomainClassifier()
            crossings = ErrorChain.crossings(e, classifiers=(classifier,))
        # inner (validation) -> outer (python) is a crossing
        assert len(crossings) == 1
        assert crossings[0].cause.domain == "validation"
        assert crossings[0].effect.domain == "python"

    def test_crossing_cause_effect_pairing(self) -> None:
        """crossings() correctly pairs cause and effect in DomainCrossing."""
        # Create a domain-error as inner and a foreign error as outer
        inner = CustomDomainError()  # domain = "custom"
        outer = ValueError("oops")
        try:
            raise outer from inner
        except ValueError as e:
            classifier = FakeDomainClassifier()
            crossings = ErrorChain.crossings(e, classifiers=(classifier,))
        # inner is the cause, outer is the effect
        assert len(crossings) == 1
        assert crossings[0].cause.type_name == "CustomDomainError"
        assert crossings[0].cause.domain == "custom"
        assert crossings[0].effect.type_name == "ValueError"
        assert crossings[0].effect.domain == "validation"

    def test_multiple_crossings(self) -> None:
        """crossings() returns multiple DomainCrossing for multi-hop chains."""
        # e1 (custom) -> e2 (validation) -> e3 (python)
        classifier = FakeDomainClassifier()
        e1 = CustomDomainError()  # "custom"
        e2 = ValueError("oops")  # "validation" via classifier
        e3 = KeyError("key")  # "python"
        try:
            try:
                try:
                    raise e1
                except CustomDomainError:
                    raise e2 from e1
            except ValueError:
                raise e3 from e2
        except KeyError as e:
            crossings = ErrorChain.crossings(e, classifiers=(classifier,))
        # custom->validation and validation->python
        assert len(crossings) == 2


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

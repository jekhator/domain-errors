"""Error chaining surface (Stage 1 single file)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol, TypeVar

from domain_errors.services.domain_error.domain_error import DomainError


TypeDomainError = TypeVar("TypeDomainError", bound=DomainError)


class ChainVia(StrEnum):
    """How a link entered the chain."""

    ROOT = "root"
    CAUSE = "cause"
    CONTEXT = "context"


class DomainClassifier(Protocol):
    """Contract a domain adapter satisfies to classify foreign errors."""

    def classify(self, err: BaseException) -> str | None:
        """Return the error's domain, or None when it is not this family."""
        ...


@dataclass(frozen=True, slots=True)
class ChainLink:
    """One hop of an exception chain, ready for structured logging."""

    type_name: str
    message: str
    code: str | None
    domain: str
    via: ChainVia

    def to_log_extra(self) -> dict[str, str | None]:
        """Return the link as a JSON-ready dict for logger extra."""
        return {
            "type": self.type_name,
            "message": self.message,
            "code": self.code,
            "domain": self.domain,
            "via": self.via.value,
        }


@dataclass(frozen=True, slots=True)
class DomainCrossing:
    """One causation hop where the error crossed from one domain to another."""

    cause: ChainLink
    effect: ChainLink

    def to_log_extra(self) -> dict[str, str | None]:
        """Return the crossing as a JSON-ready dict for logger extra."""
        return {
            "cause_type": self.cause.type_name,
            "cause_domain": self.cause.domain,
            "effect_type": self.effect.type_name,
            "effect_domain": self.effect.domain,
        }


class ErrorChain:
    """Stateless chaining operations for typed domain errors."""

    @staticmethod
    def wrap(
        err: Exception,
        *,
        as_: type[TypeDomainError],
        message: str | None = None,
        **context: object,
    ) -> TypeDomainError:
        """Construct a typed domain error for the caller to raise with from err."""
        return as_(message=message, **context)

    @staticmethod
    def history(
        err: BaseException,
        classifiers: tuple[DomainClassifier, ...] = (),
    ) -> tuple[ChainLink, ...]:
        """Walk the full exception cascade into links, the error itself first."""
        links: list[ChainLink] = []
        seen: set[int] = set()
        current: BaseException | None = err
        via = ChainVia.ROOT
        while current is not None and id(current) not in seen:
            seen.add(id(current))
            links.append(
                ChainLink(
                    type_name=current.__class__.__name__,
                    message=str(current),
                    code=getattr(current, "code", None),
                    domain=ErrorChain._domain_of(current, classifiers),
                    via=via,
                )
            )
            if current.__cause__ is not None:
                current = current.__cause__
                via = ChainVia.CAUSE
            elif not current.__suppress_context__:
                current = current.__context__
                via = ChainVia.CONTEXT
            else:
                current = None
        return tuple(links)

    @staticmethod
    def crossings(
        err: BaseException,
        classifiers: tuple[DomainClassifier, ...] = (),
    ) -> tuple[DomainCrossing, ...]:
        """Return the causation hops where the cascade crossed domains."""
        links = ErrorChain.history(err, classifiers)
        found: list[DomainCrossing] = []
        for effect, cause in zip(links, links[1:]):
            if cause.domain != effect.domain:
                found.append(DomainCrossing(cause=cause, effect=effect))
        return tuple(found)

    @staticmethod
    def _domain_of(
        err: BaseException, classifiers: tuple[DomainClassifier, ...]
    ) -> str:
        """Resolve an error's domain from its contract or the first matching classifier."""
        domain = getattr(err, "domain", None)
        if isinstance(domain, str):
            return domain
        for classifier in classifiers:
            verdict = classifier.classify(err)
            if verdict is not None:
                return verdict
        return "python"

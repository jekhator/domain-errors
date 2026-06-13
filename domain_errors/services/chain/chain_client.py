"""Error chaining operations: wrap, history, crossings."""

from __future__ import annotations

from typing import TypeVar

from domain_errors.domains.domain_error.domain_error import DomainError
from domain_errors.services.constants import chain as const

from .chain_objects import ChainLink
from .chain_objects import ChainVia
from .chain_objects import DomainClassifier
from .chain_objects import DomainCrossing


TypeDomainError = TypeVar("TypeDomainError", bound=DomainError)


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
                    context=getattr(current, "context", {}),
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
        return const.DEFAULT_DOMAIN

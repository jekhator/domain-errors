"""Error chaining surface (Stage 1 single file)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeVar

from domain_errors.services.domain_error.domain_error import DomainError


TypeDomainError = TypeVar("TypeDomainError", bound=DomainError)


@dataclass(frozen=True, slots=True)
class ChainLink:
    """One hop of a PEP 3134 cause chain, ready for structured logging."""

    type_name: str
    message: str
    code: str | None

    def to_log_extra(self) -> dict[str, str | None]:
        """Return the link as a JSON-ready dict for logger extra."""
        return {"type": self.type_name, "message": self.message, "code": self.code}  # noqa: dto-strict-R002


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
    def history(err: BaseException) -> tuple[ChainLink, ...]:
        """Walk the PEP 3134 cause chain into links, the error itself first."""
        links: list[ChainLink] = []
        current: BaseException | None = err
        while current is not None:
            links.append(
                ChainLink(
                    type_name=current.__class__.__name__,
                    message=str(current),
                    code=getattr(current, "code", None),
                )
            )
            current = current.__cause__
        return tuple(links)

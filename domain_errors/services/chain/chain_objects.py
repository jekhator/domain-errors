"""Error chaining value objects: links, crossings, via tags, and the classifier contract."""

from __future__ import annotations

from dataclasses import asdict
from dataclasses import dataclass
from dataclasses import field
from enum import StrEnum
from typing import Protocol


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
class LinkLogExtra:
    """Structured-logging payload for one chain link."""

    type: str
    message: str
    code: str | None
    domain: str
    via: str
    context: dict[str, object]


@dataclass(frozen=True, slots=True)
class CrossingLogExtra:
    """Structured-logging payload for one cross-domain crossing."""

    cause_type: str
    cause_domain: str
    effect_type: str
    effect_domain: str


@dataclass(frozen=True, slots=True)
class ChainLink:
    """One hop of an exception chain, ready for structured logging."""

    type_name: str
    message: str
    code: str | None
    domain: str
    via: ChainVia
    context: dict[str, object] = field(default_factory=dict, compare=False)

    def to_log_extra(self) -> dict[str, object]:
        """Return the link as a JSON-ready dict for logger extra."""
        return asdict(
            LinkLogExtra(
                type=self.type_name,
                message=self.message,
                code=self.code,
                domain=self.domain,
                via=self.via.value,
                context=self.context,
            )
        )


@dataclass(frozen=True, slots=True)
class DomainCrossing:
    """One causation hop where the error crossed from one domain to another."""

    cause: ChainLink
    effect: ChainLink

    def to_log_extra(self) -> dict[str, object]:
        """Return the crossing as a JSON-ready dict for logger extra."""
        return asdict(
            CrossingLogExtra(
                cause_type=self.cause.type_name,
                cause_domain=self.cause.domain,
                effect_type=self.effect.type_name,
                effect_domain=self.effect.domain,
            )
        )

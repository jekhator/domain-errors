"""Error chaining: typed wrap, full cascade history, and cross-domain crossings (ErrorChain + ChainLink/DomainCrossing value objects)."""

from .chain_client import ErrorChain as ErrorChain
from .chain_objects import ChainLink as ChainLink
from .chain_objects import ChainVia as ChainVia
from .chain_objects import DomainClassifier as DomainClassifier
from .chain_objects import DomainCrossing as DomainCrossing

__all__ = [
    "ChainLink",
    "ChainVia",
    "DomainClassifier",
    "DomainCrossing",
    "ErrorChain",
]

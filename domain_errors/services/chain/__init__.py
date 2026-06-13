"""Error chaining: typed wrap, full cascade history, and cross-domain crossings (ErrorChain + ChainLink/DomainCrossing value objects)."""

from domain_errors.services.chain.chain_client import ErrorChain
from domain_errors.services.chain.chain_objects import (
    ChainLink,
    ChainVia,
    DomainClassifier,
    DomainCrossing,
)

__all__ = ["ChainLink", "ChainVia", "DomainClassifier", "DomainCrossing", "ErrorChain"]

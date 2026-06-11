# Diagrams

> **Location:** `domain-errors/docs/apps/diagrams.md`
> **Status:** Design locked; implementation in progress.

## Error Class Hierarchy & Chaining

```
domain_errors/services/domain_error/domain_error.py
═══════════════════════════════════════════════════════════════════════
[EXCEPTION]

┌─ DomainError(Exception) ──────────────────────────────────────────┐
│   @classvar contract:                                             │
│     code: str = "domain_error"                                    │
│     http_status: int = 500                                        │
│     retryable: bool = False                                       │
│     default_message: str                                          │
│                                                                   │
│   Instance state:                                                 │
│     message: str                                                  │
│     context: dict[str, Any]                                       │
│                                                                   │
│   [mth] __init__(self, message: str | None = None, **context)   │
│         → None                                                    │
│         Initialize exception with optional message override and   │
│         arbitrary context kwargs                                 │
│                                                                   │
│   Base exception class for domain-specific errors in consumer     │
│   projects                                                        │
└───────────────────────────────────────────────────────────────────┘
```

## Error Chaining Service

```
domain_errors/services/chain/chain.py
═══════════════════════════════════════════════════════════════════════

TError = TypeVar("TError", bound=DomainError)

┌─ [FROZEN] ChainLink ──────────────────────────────────────────────┐
│   type_name: str                                                  │
│   message: str                                                    │
│   code: str | None                                                │
│                                                                   │
│   [mth] to_log_extra(self) → dict[str, str | None]              │
│         Convert this link to logging extra dict for structured   │
│         logging backends                                         │
│                                                                   │
│   Immutable causal link in an exception chain                    │
└───────────────────────────────────────────────────────────────────┘


domain_errors/services/chain/chain.py
───────────────────────────────────────────────────────────────────────

┌─ [SERVICE] ErrorChain (stateless) ────────────────────────────────┐
│   [static] wrap(                                                  │
│       err: BaseException,                                         │
│       *,                                                          │
│       as_: type[TError],                                          │
│       message: str | None = None,                                │
│       **context                                                   │
│     ) → TError                                                    │
│     Wrap an exception into a typed domain error, preserving       │
│     causal chain via PEP 3134 (raise … from err). Consumer       │
│     projects define root subclasses (e.g. class MyProjectError    │
│     (DomainError)) and per-layer subtrees; retry middleware      │
│     keys off retryable.                                           │
│                                                                   │
│   [static] history(                                               │
│       err: BaseException                                          │
│     ) → tuple[ChainLink, ...]                                    │
│     Extract causal chain as an immutable tuple of ChainLinks,    │
│     in order from originating exception to current (self first).  │
│                                                                   │
│   Stateless utility for PEP 3134 exception chaining              │
└───────────────────────────────────────────────────────────────────┘
```

## Public API

```
domain_errors/__init__.py
═══════════════════════════════════════════════════════════════════════

Exports:
  DomainError           ← base exception class
  ChainLink             ← immutable causal chain link
  chain                 ← alias for ErrorChain.wrap
  chain_history         ← alias for ErrorChain.history
  __version__           ← package version string

Usage pattern (consumer projects):

  # 1. Define root subclass in your project
  class MyProjectError(DomainError):
      contract = DomainError.contract

  # 2. Per-layer subtrees (e.g. API, domain, data)
  class ApiError(MyProjectError):
      contract = {...}

  class ValidationError(ApiError):
      contract = {code="validation_error", http_status=400, retryable=False}

  # 3. Raise with chaining
  try:
      upstream_call()
  except ValueError as err:
      raise chain(err, as_=ValidationError, user_input=value) from err

  # 4. Access history in error handler
  history = chain_history(exc)  # tuple[ChainLink, ...]
```

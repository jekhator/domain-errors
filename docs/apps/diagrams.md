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
│     domain: str = "application"                                   │
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
│   projects. domain classvar is open taxonomy; consumers declare   │
│   their own like "cloud", "billing", "network", etc.             │
└───────────────────────────────────────────────────────────────────┘
```

## Error Chaining Service

```
domain_errors/services/chain/chain.py
═══════════════════════════════════════════════════════════════════════

TError = TypeVar("TError", bound=DomainError)

┌─ [ENUM] ChainVia(StrEnum) ────────────────────────────────────────┐
│   ROOT = "root"       (exception chain started here)              │
│   CAUSE = "cause"     (linked via __cause__ per PEP 3134)        │
│   CONTEXT = "context" (linked via __context__ per PEP 3134)      │
│                                                                   │
│   How a link entered the chain                                   │
└───────────────────────────────────────────────────────────────────┘


┌─ [PROTOCOL] DomainClassifier ─────────────────────────────────────┐
│   [mth] classify(err: BaseException) → str | None                │
│         Inspect exception and return its domain string or None    │
│         when this classifier does not recognize the family.       │
│         Adapter's verdict; composable.                            │
│                                                                   │
│   Adapter model: one classifier per foreign error family          │
└───────────────────────────────────────────────────────────────────┘


┌─ [FROZEN] ChainLink ──────────────────────────────────────────────┐
│   type_name: str                                                  │
│   message: str                                                    │
│   code: str | None                                                │
│   domain: str                                                     │
│   via: ChainVia                                                   │
│                                                                   │
│   [mth] to_log_extra(self) → dict[str, str | None]              │
│         Convert this link to logging extra dict for structured   │
│         logging backends                                         │
│                                                                   │
│   Immutable causal link in an exception chain; domain and via    │
│   enable cross-domain causation tracking                         │
└───────────────────────────────────────────────────────────────────┘


┌─ [FROZEN DTO] DomainCrossing ────────────────────────────────────┐
│   cause: ChainLink                                                │
│   effect: ChainLink                                               │
│                                                                   │
│   [mth] to_log_extra(self) → dict[str, Any]                     │
│         Convert this crossing to logging extra for structured    │
│         logging; includes domain pair (cause.domain →            │
│         effect.domain)                                           │
│                                                                   │
│   One cross-domain causation hop (cause and effect in different  │
│   domains)                                                        │
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
│       err: BaseException,                                         │
│       classifiers: tuple[DomainClassifier, ...] = ()             │
│     ) → tuple[ChainLink, ...]                                    │
│     Extract causal chain as an immutable tuple of ChainLinks,    │
│     in order from originating exception to current. Walks __cause__│
│     first, then __context__ unless suppressed (matching Python's │
│     traceback rules). Cycle-guarded; each link is tagged via      │
│     (ROOT/CAUSE/CONTEXT). Classifiers run in order; first match  │
│     wins; missing match defaults to "application".                │
│                                                                   │
│   [static] crossings(                                             │
│       err: BaseException,                                         │
│       classifiers: tuple[DomainClassifier, ...] = ()             │
│     ) → tuple[DomainCrossing, ...]                               │
│     Adjacent pairs of history links whose domains differ.         │
│     Models causation hops between domains (e.g. database →        │
│     validation → api). Use for audit/telemetry.                  │
│                                                                   │
│   Stateless utility for PEP 3134 exception chaining with domain  │
│   awareness                                                       │
└───────────────────────────────────────────────────────────────────┘
```

## Domain Classifiers

```
domain_errors/domains/
═══════════════════════════════════════════════════════════════════════

Adapter model: one classifier module per foreign error family.
Each exports a DomainClassifier instance.

┌─ domains/python.py ───────────────────────────────────────────────┐
│   Classifies stdlib exception families:                           │
│     OSError / FileNotFoundError / PermissionError → "os"         │
│     ConnectionError / TimeoutError → "network"                    │
│     ValueError / KeyError / TypeError → "logic"                   │
│     AssertionError → "assertion"                                  │
│   Status: in progress                                             │
└───────────────────────────────────────────────────────────────────┘

┌─ domains/http.py ────────────────────────────────────────────────┐
│   Planned: httpx / requests exception families                    │
│     httpx.HTTPError → "http"                                      │
│     httpx.TimeoutException → "http"                               │
│     requests.RequestException → "http"                            │
│   Status: planned                                                 │
└───────────────────────────────────────────────────────────────────┘

┌─ domains/botocore.py ────────────────────────────────────────────┐
│   Planned: botocore exception families                            │
│     botocore.exceptions.ClientError → "cloud"                    │
│     botocore.exceptions.ConnectionError → "cloud"                │
│   Status: planned                                                 │
└───────────────────────────────────────────────────────────────────┘
```

## Public API

```
domain_errors/__init__.py
═══════════════════════════════════════════════════════════════════════

Exports:
  DomainError           ← base exception class
  ChainLink             ← immutable causal chain link
  ChainVia              ← enum for chain entry mode (ROOT/CAUSE/CONTEXT)
  DomainClassifier      ← protocol for exception family adapters
  DomainCrossing        ← frozen DTO for cross-domain causation hops
  chain                 ← alias for ErrorChain.wrap
  chain_history         ← alias for ErrorChain.history
  chain_crossings       ← alias for ErrorChain.crossings
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

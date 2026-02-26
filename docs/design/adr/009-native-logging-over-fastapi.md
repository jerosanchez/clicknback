# ADR 009: Use Python's Native Logging Over FastAPI/Uvicorn Logging

## Status

Accepted

## Context

A FastAPI application runs under a server (Uvicorn) that configures its own logging infrastructure. FastAPI also exposes integration points with Uvicorn's log configuration via `log_config` and `access_log` parameters in `uvicorn.run()`. The question is: should ClickNBack's application-level logging be expressed through that mechanism, or through Python's standard `logging` module configured independently?

### Option 1: Uvicorn/FastAPI Log Configuration

```python
# main.py
import uvicorn

uvicorn.run(
    app,
    log_config={
        "version": 1,
        "formatters": {
            "default": {"format": "%(asctime)s - %(levelname)s - %(message)s"}
        },
        "handlers": {
            "default": {"class": "logging.StreamHandler", "formatter": "default"}
        },
        "loggers": {
            "uvicorn": {"handlers": ["default"], "level": "INFO"},
            "uvicorn.error": {"level": "INFO"},
            "uvicorn.access": {"level": "INFO"},
        },
    },
)
```

- ✅ Integrated with Uvicorn's own log output
- ❌ Couples application logging configuration to the server process startup
- ❌ Not available when running under alternative servers (Gunicorn, Hypercorn) or in tests
- ❌ Cannot be configured before the application starts (e.g., from environment variables at import time)
- ❌ Harder to add custom formatters or handlers per environment

### Option 2: Python Standard `logging` Module (Configured at Import Time)

```python
# app/core/logging.py
import logging
from app.core.config import settings

class ExtraDictFormatter(logging.Formatter):
    def format(self, record):
        extras = {k: v for k, v in record.__dict__.items() if k not in standard_attrs}
        base = super().format(record)
        return f"{base} | extra={extras}" if extras else base

handler = logging.StreamHandler()
handler.setFormatter(ExtraDictFormatter(fmt="%(asctime)s - %(levelname)s - %(name)s - %(message)s"))

root_logger = logging.getLogger()
root_logger.setLevel(getattr(logging, settings.log_level))
root_logger.handlers.clear()
root_logger.addHandler(handler)
```

- ✅ Fully independent of the server layer — works identically in tests, scripts, and any ASGI server
- ✅ Configured from environment variables through `Settings`, consistent with the rest of the app
- ✅ Full control over formatters, handlers, and log levels per environment
- ✅ Custom formatter (e.g., `ExtraDictFormatter`) can append structured `extra={}` context to every log line
- ✅ Named loggers (`logging.getLogger(__name__)`) carry module identity into every log line
- ❌ Uvicorn's own access and error logs are managed separately; both need to be aligned if needed

## Decision

Configure all application logging using **Python's standard `logging` module**, centralised in `app/core/logging.py`. This module:

1. Defines a custom `ExtraDictFormatter` that serialises any `extra={}` keyword arguments to the end of each log line.
2. Attaches a `StreamHandler` to the root logger, replacing any handlers installed by Uvicorn or other libraries.
3. Reads the log level from `settings.log_level` (an environment variable), so it can differ between environments without any code change.
4. Exports a module-level `logger = logging.getLogger(__name__)` for use by infrastructure code, and re-exports the `logging` module itself for use by API-layer modules that prefer the module-level call style.

All feature modules import from `app.core.logging` rather than from the standard library directly, ensuring the configured formatter and handler are always in effect.

## Consequences

- ✅ Logging behaviour is identical in all execution contexts: application server, CLI scripts, and the test suite.
- ✅ Structured context (`extra={}`) is preserved and rendered consistently without depending on any third-party library.
- ✅ Log level is controlled by a single environment variable and takes effect without restarting or reconfiguring a server.
- ✅ Custom formatters (e.g., switching to JSON output for a log aggregator) require a change in one file only.
- ✅ Tests can inspect log output directly via pytest's `caplog` fixture without any server bootstrapping.
- ⚠️ Uvicorn's access log and error log are independent loggers; if access logging is required, Uvicorn's `access_log` logger must be configured explicitly in `core/logging.py` as well.
- ⚠️ `root_logger.handlers.clear()` removes any handlers installed by third-party libraries before this module is imported; this is intentional but should be documented to avoid confusion.

## Alternatives Considered

### Structlog

- **Pros:** Powerful pipeline-based structured logging, JSON output and context binding built-in.
- **Cons:** Additional dependency, non-trivial learning curve, integration with stdlib `logging` requires bridging. Overkill for the current scale.
- **Rejected:** Standard `logging` with the custom formatter meets the project's needs without adding a dependency.

### FastAPI's `lifespan` Hook for Logger Setup

- **Pros:** Logger configuration is co-located with app startup.
- **Cons:** Logging would not be active during module imports that happen before `lifespan` runs; not available in tests that bypass `lifespan`.
- **Rejected:** Import-time configuration in `core/logging.py` is simpler and more robust.

## Rationale

Python's `logging` module is deliberately framework-agnostic. Tying log configuration to a server process would make the application harder to test and less portable. Configuring logging once, at import time, in a dedicated infrastructure module keeps the concern well-contained, ensures consistent output everywhere, and allows the formatter to evolve independently of application code.

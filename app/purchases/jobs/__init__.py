"""Purchase background jobs.

Each sub-package contains one background job following the Fan-Out Dispatcher
+ Per-Item Runner pattern (ADR-016).  Jobs are wired in
``app/purchases/composition.py`` and scheduled in ``app/main.py``.
"""

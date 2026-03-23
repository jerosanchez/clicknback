# ClickNBack – Quality Gates

This document is the authoritative reference for code quality enforcement in the ClickNBack project. It applies to **every change** — new features, bug fixes, refactors, schema updates, policy tweaks, test additions, and documentation edits alike. No task is complete until all quality gates pass.

---

## 1. The Mandatory Command Sequence

After making any modification to the repository, run the following sequence from the project root before reporting the task as done:

```bash
make lint && make test && make coverage && make security
```

All four commands must exit with code 0. If any of them fails, fix the issue and re-run the full sequence from the start. Do not stop mid-sequence or skip a gate.

**Pre-commit hooks (one-time local setup):** The same gates also run automatically before every `git commit` via pre-commit hooks. Run this once after cloning the repo:

```bash
pre-commit install
```

After that, every commit is automatically checked. To run the hooks manually against the entire codebase at any time:

```bash
pre-commit run --all-files
```

---

## 2. What Each Gate Does

### `make lint`

Runs three checkers in order:

| Tool | Scope | What it enforces |
| --- | --- | --- |
| `markdownlint` | `**/*.md` | Markdown style and structure (heading hierarchy, blank lines, list formatting, line length, etc.) |
| `flake8` | `app/` | PEP 8 compliance, undefined names, unused imports, max line length of 88 characters |
| `isort --check-only` | `app/` | Import ordering (black-compatible profile, 88-char line length). Fails if imports are not sorted correctly |
| `black --check` | `app/` | Code formatting. Fails if any file would be reformatted by black |

`make lint` is read-only — it checks but does not modify files.

### `make test`

Runs the full pytest suite with line-level coverage:

```bash
python -m pytest tests/ --cov=app --cov-report=term-missing --cov-report=html --cov-report=xml
```

All tests must pass. Three reports are generated:

- `htmlcov/` — human-readable HTML for browser inspection
- `coverage.xml` — machine-readable XML consumed by CI coverage gate
- Terminal output — visible inline during the run

### `make coverage`

Runs the full test suite, captures output to `coverage.txt`, then runs `scripts/coverage-grade.sh` to print an emoji-graded result:

| Coverage | Grade |
| --- | --- |
| `< 50%` | ❌ Poor — significant gaps, must improve |
| `50–69%` | ⚠️ Low — almost there, keep going |
| `70–79%` | ✅ Approved — minimum bar cleared |
| `80–89%` | 🌟 High — above expectations |
| `≥ 90%` | 🚀 Excellent — outstanding coverage |

**Hard gate: 85%.** `make coverage` exits non-zero below 85%, failing CI and blocking the commit-close sequence. **80% is the aspirational target** — the grade scale makes it visible at a glance without reading numbers.

### `make security`

Runs Bandit static analysis on `app/`:

```bash
bandit -r app/ -ll
```

The `-ll` flag reports only **medium and high severity** issues. Low-severity noise is filtered out. Scope is limited to `app/` — tests and seeds are excluded. Exits non-zero if any medium or high severity finding is present.

Do not suppress findings with `# nosec` without a documented reason.

### `pre-commit run --all-files`

Runs all pre-commit hooks against every file in the repository:

| Hook | What it checks |
| --- | --- |
| `trailing-whitespace` | No trailing spaces |
| `end-of-file-fixer` | Files end with a newline |
| `check-yaml` | YAML syntax |
| `check-added-large-files` | No accidentally committed large files |
| `black` | Code formatting |
| `isort` | Import ordering |
| `flake8` | PEP 8 + undefined names |
| `bandit` | Security scan (medium/high severity) |

Hooks run automatically on every `git commit` after `pre-commit install`. Use `pre-commit run --all-files` when first setting up or after updating hook versions.

---

## 3. Mandatory Workflow

Follow this sequence for every task, no matter how small:

1. **Implement the change** following the project conventions in `feature-architecture.md`.
2. **Run the full gate sequence** from the project root (see Section 7 Quick Reference for the exact command).
3. **Fix every failure autonomously** — see Section 4 for specific remedies.
4. **Re-run the full sequence** until all four gates exit with code 0.
5. **Only then report the task as complete** to the user.

Never hand control back to the user while any gate is failing. Never ask the user to run the quality gates themselves.

### CI Job Order

The same gates run in GitHub Actions on every pull request and push to `main`, as sequential jobs that each depend on the previous:

```text
lint → test → coverage → security
```

Each job is separate so failure reasons are unambiguous in the Actions UI: a red `coverage` job means the threshold was missed; a red `security` job means a Bandit finding was introduced — neither is conflated with broken tests.

---

## 4. Diagnosing and Fixing Failures

### 4.1 `markdownlint` Failures

Markdownlint checks all `.md` files in the repository, including files under `docs/`.

Common violations and fixes:

| Violation | Typical cause | Fix |
| --- | --- | --- |
| `MD022` – Headings must be surrounded by blank lines | Missing blank line before or after a `#` heading | Add a blank line above and below every heading |
| `MD031` – Fenced code blocks must be surrounded by blank lines | Code block directly follows or precedes text | Add a blank line before the opening fence and after the closing fence |
| `MD032` – Lists must be surrounded by blank lines | List starts or ends without a surrounding blank line | Add blank lines |
| `MD013` – Line too long | Prose line exceeds configured limit | Wrap the line |
| `MD041` – First line must be a top-level heading | File does not start with `# Title` | Add the heading or check the file structure |

See `docs/guidelines/markdown-docs.md` for the project's full markdown conventions.

### 4.2 `flake8` Failures

Flake8 checks Python style and correctness. Common violations:

| Code | Meaning | Fix |
| --- | --- | --- |
| `F401` | Imported but unused | Remove the unused import |
| `F811` | Redefinition of unused name | Remove the duplicate definition or the earlier unused one |
| `E501` | Line too long (> 88 chars) | Break the line; use implicit continuation inside `()` or `[]` |
| `E302 / E303` | Wrong number of blank lines between top-level definitions | Add or remove blank lines as required |
| `F841` | Local variable assigned but never used | Remove the assignment or use the variable |
| `W291 / W293` | Trailing whitespace | Remove trailing spaces |

**Do not add `# noqa` suppression comments** unless the violation is a genuine false-positive and the reason is documented inline.

### 4.3 Test Failures

Identify the root cause before acting on any test failure. Follow this decision tree:

```text
Test fails
  ├─ Was the test correct before my change?
  │   ├─ YES → I broke existing behavior → fix the implementation to restore it
  │   └─ NO  → Test was already broken (pre-existing) → fix the test to match correct behavior
  │
  ├─ Is this a new test I wrote?
  │   └─ Fix the test or the implementation so they agree on the correct behavior
  │
  └─ Is this an indirect breakage (e.g., I changed a shared fixture or schema)?
      └─ Fix every affected test; do not patch individual assertions in isolation
```

**Never do any of the following to make a failing test pass:**

- Add `@pytest.mark.skip` or `@pytest.mark.xfail`.
- Delete the test.
- Stub out the implementation with a dummy return value.
- Catch and swallow the exception that the test is asserting.

If a test reveals that the intended behavior is genuinely ambiguous, implement the behavior that best satisfies the feature specification and update the test to document it explicitly.

### 4.4 Import / Syntax Errors

When `pytest` fails at collection time (before any test runs), identify the failing file from the traceback and fix the syntax error or broken import. Rerun `make test` to confirm collection succeeds.

Common causes:

- Circular imports introduced by a new `composition.py` wiring.
- Missing `__init__.py` in a new module directory.
- A class or function referenced before it is defined.
- A typo in an import path.

### 4.5 Migration / Model Drift

If tests fail because of a missing column or table, the ORM model was changed but no Alembic migration was generated. Fix by:

1. Confirm the model is imported in `app/models.py`.
2. Generate the migration: `alembic revision --autogenerate -m "<description>"`.
3. Apply it: `alembic upgrade head`.
4. Re-run `make test`.

---

## 5. Scope of Application

The quality gate requirement applies without exception to:

| Change type | Applies? |
| --- | --- |
| New feature module | Yes — always (see `feature-architecture.md` Step 13) |
| Bug fix | Yes |
| Refactor (no behavior change) | Yes |
| Schema / model change | Yes |
| Policy or service update | Yes |
| New or modified test | Yes |
| Documentation (`.md`) change | Yes — `make lint` checks markdown too |
| `composition.py` wiring change | Yes |
| `main.py` router registration | Yes |
| Alembic migration script | Yes |

The only files excluded from Python linting and formatting are those outside `app/` (e.g., `alembic/`, `tests/`, `seeds/`). However, `tests/` is still exercised by `make test`, and all `.md` files are still checked by `markdownlint`.

---

## 6. Handling Pre-existing Failures

If, upon running the quality gates, failures are detected that pre-date the current task:

1. **Lint / formatting failures in files outside the current change** — fix them. Style debt is always in scope.
2. **Test failures that pre-date the change** — fix them if the root cause is clear. If the failure is complex and unrelated to the current task, document it in the task report and flag it explicitly; do not silently ignore it.
3. **Never leave the repository in a worse state than you found it.** If you cannot fix a pre-existing failure without significantly expanding scope, at minimum do not introduce additional failures.

---

## 7. Quick Reference

```bash
# Run all quality gates (full sequence)
make lint && make test && make coverage && make security

# Run only tests (useful mid-fix iteration)
make test

# Run coverage with graded output (includes test run)
make coverage

# Run Bandit security scan
make security

# Run all pre-commit hooks against the whole repo
pre-commit run --all-files

# One-time local setup: install pre-commit hooks into .git
pre-commit install

# Run a single test file during debugging
source .venv/bin/activate && python -m pytest tests/<module>/test_<file>.py -v

# Run tests matching a name pattern
source .venv/bin/activate && python -m pytest tests/ -k "<test_name_substring>" -v
```

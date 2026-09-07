# Copilot instructions for fintrack-api
# Copilot instructions for fintrack-api

Purpose: Give AI coding agents the minimum, actionable context to work productively in this repository.

Quick orientation
- Root layout: `src/transactions/` (domain code), `tests/` (unit/integration tests), and top-level docs: `README.md`, `ARCHITECTURE.md`, `PROMPTS.md`, `TOOL_STRATEGY.md`, `PR_DESCRIPTION.md`, `REVIEW.md`.
- Primary focus: transaction domain logic under `src/transactions/` — treat files there as single-responsibility modules that implement business rules for transaction types.

What to do first (concrete)
- Read `ARCHITECTURE.md` then `src/transactions/` to understand component boundaries before making changes.
- When adding a new transaction handler or domain file, create `src/transactions/<name>.py` and a matching test `tests/test_<name>.py` that exercises both happy path and key edge cases.
- Update `ARCHITECTURE.md` and `README.md` when you introduce new components or public APIs.

Code patterns and conventions (discoverable)
- Tests mirror the module layout: module `src/transactions/foo*` => tests in `tests/test_foo*`.
- Keep domain code in `src/transactions/` and avoid placing side-effecting code (DB, network, persistence) directly inside pure business-rule functions — centralize I/O in thin adapters.
- Small, focused functions that accept plain data structures are easier to test. Tests in `tests/` are the source of truth for expected behavior.

Developer workflows (how we typically run things)
- Inspect `tests/` first to see expected behavior. Run tests with `pytest`.

Project-specific conventions

- Tech stack: Python 3.10+, FastAPI, SQLAlchemy ORM, Pydantic for validation, pytest for tests.
- Auth in API: use `X-User-Id` header for identifying caller in this prototype; enforce service-level checks `request_user_id == target_user_id` before returning user data.
- DB config: respect `FINTRACK_DATABASE_URL` env var; default to local SQLite for development. Use SQLAlchemy sessions from `src/transactions/repository.py`.
- Validation: prefer Pydantic models for input validation and raise explicit `ValidationError` for service-level checks.
- Logging: use structured logging (not yet enforced here). Redact PII in logs.

Testing & CI

- Tests mirror module structure: `src/transactions/foo.py` -> `tests/test_foo.py`.
- Run tests locally with:

```bash
python -m pytest -q
```

- Every change to business logic must include unit tests that cover happy paths and expected failures (validation/authorization errors).

Prompting guidelines for Copilot

- Before accepting Copilot code: ensure it includes input validation, explicit auth checks, no unguarded destructive operations, and uses the project DB config.
- When asking Copilot to scaffold APIs, include the exact header `X-User-Id` in the prompt and request Pydantic models for inputs.

When to ask the human

- If the runtime, CI commands, or DB connection conventions are unclear, ask the repo owner.

Maintenance rules for this file
- Update this file when toolchain or test commands change, or when project layout changes (new top-level packages, services, or infra).

Links to inspect
- `ARCHITECTURE.md` — high-level components and dataflows.
- `src/transactions/` — domain logic.
- `tests/` — unit/integration expectations.
- `PR_DESCRIPTION.md`, `REVIEW.md` — PR and review conventions.

If anything in here is ambiguous, ask the repo owner for runtime/test commands and any service credentials needed for integration tests.

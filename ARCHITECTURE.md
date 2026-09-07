# FinTrack API  Architecture Overview

This service implements FinTrack domain logic with a layered architecture to keep business rules testable and side effects isolated.

Layers
- API layer: `src/main.py` (FastAPI)  HTTP endpoints, request parsing, and simple auth gate (header-based during this exercise).
- Service layer: `src/transactions/service.py`  business rules (transaction processing, expense splitting, balance calculation) and input validation.
- Repository layer: `src/transactions/repository.py`  ORM-backed data access (SQLAlchemy) and session management.
- Models: `src/transactions/models.py`  SQLAlchemy declarative models (`SharedExpense`, `Transaction`).

Data flow
- Client -> FastAPI endpoint (auth header) -> Service (validation, authorization) -> Repository (ORM persistence) -> DB

Why this fits fintech
- Clear separation of concerns enables strong validation, audit logging, and replaces persistence layer for secure storage and migrations; this reduces risk for financial data handling.

Key decisions
- Use SQLAlchemy ORM with a configurable DB URL (env var) for predictable migrations and pooling.
- Keep side effects out of pure business functions to simplify testing and review.


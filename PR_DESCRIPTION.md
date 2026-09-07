# PR Description Template

Summary:
- What changed and why (1-2 sentences)

Related docs:
- Link to updated `ARCHITECTURE.md` or `README.md` if applicable.

Testing:
- How to run tests locally (see `tests/`) and any manual verification steps.

Risks & rollbacks:
- List any migration or integration concerns and a rollback plan.

---

Summary of this change
- Adds remediated Transaction module and Expense Splitting feature (FastAPI endpoints, SQLAlchemy models, services) plus tests and documentation.

AI Tool Disclosure
- Copilot features used: inline suggestions (completion), chat/completion for design prompts. Initial unreviewed Transaction files were generated with the prompt: "Generate a Transaction model and a Transaction service with create, get-by-user, and delete-all functions. Use a database." Those raw files were saved verbatim and then remediated. Estimated AI-generated vs hand-written: ~40% AI snippets accepted and adapted, ~60% hand-written and reviewed.

Testing coverage & gaps
- Tests added: `tests/test_expense_splitting.py` covering equal split, custom split valid/invalid, net balance, single-participant edge case, and missing auth header.
- Known gaps: no load/concurrency tests; persistence and CI integration should be verified with the chosen production DB.

Risk / Trade-off
- Trade-off: Simplified balance model (creator-paid model) chosen for clarity; does not track who actually paid shares beyond creator assumption. This reduces complexity but may not fit scenarios where expenses are paid by multiple participants.

Self-review checklist
- [x] Ran unit tests locally with `pytest`.
- [x] Verified validation for split types and amounts.
- [x] Confirmed authorization header is required for API endpoints.

Peer Review Simulation

Comment 1 (security): "File: `src/transactions/service.py`  Please add structured logging with a correlation ID for each API call and redact PII (user IDs) in logs. This helps incident investigation and meets compliance requirements."

Comment 2 (correctness): "File: `src/transactions/service.py` line where equal split is computed  use precise distribution strategy: rounding shares may leave a remainder; prefer assigning the remainder to the creator or a deterministic participant to keep sums exact. Add a unit test for remainder handling."

Comment 3 (AI-specific): "File: `src/transactions/transaction_service.py` (original unreviewed file)  Copilot generated a `delete_all_transactions` function. Remove or restrict this operation and ensure any destructive admin operation requires explicit confirmation and audit logging. AI tends to suggest convenience utilities that are unsafe in production."


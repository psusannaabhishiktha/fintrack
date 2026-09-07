# Prompt examples and templates

- New transaction type:
  "Create `src/transactions/<name>.py` implementing `<public_fn>(input: dict) -> dict`. Add `tests/test_<name>.py` with a success case and at least one failure case. Abstract I/O behind an adapter named `<name>_adapter`." 

- Small refactor:
  "Refactor `src/transactions/<file>.py` to extract validation into `validate_<thing>()` and add tests demonstrating previous behaviors remain unchanged. Keep function signatures stable."

---

Case Study Prompt Chain (exact prompts used)

1) Raw AI-generated Transaction module (saved verbatim):
"Generate a Transaction model and a Transaction service with create, get-by-user, and delete-all functions. Use a database."

2) Remediation scaffolding prompts (used with Copilot suggestions while authoring remediated code):
- "Create SQLAlchemy models for transactions and shared expenses with JSON participants field." (Feature: Copilot inline suggestions)
- "Add a repository class with `create_shared_expense` and `list_all_expenses` using SQLAlchemy session." (Feature: Copilot inline)
- "Implement an ExpenseService with Pydantic validation and balance calculation for equal and custom splits." (Feature: Copilot inline)
- "Create FastAPI endpoints: POST /expenses and GET /balances, using header X-User-Id for auth." (Feature: Copilot inline)

Copilot features used (simulated here):
- Inline suggestions while editing files (auto-complete snippets).
- Chat/completion prompts for generating function-level implementations.

Prompting techniques applied
- Specificity: Provided exact function names and field lists for shared expense model (e.g., `participants` list of `{user_id, amount}`).
- Constraint: Constrained output to use an ORM and Pydantic validation.
- Decomposition: Broke the problem into smaller prompts (models  repository  service  API) and iterated.
- Iterative refinement: Reviewed Copilot outputs, ran tests, and re-prompted to fix failing cases.

Post-Generation Corrections
- Replaced raw sqlite3 usage with SQLAlchemy and added `SessionLocal` and `init_db()`.
- Added Pydantic models and explicit validation for `split_type`, participant count, and amount sums.
- Implemented authorization via `X-User-Id` header and enforced data access boundaries in service layer.
- Removed/guarded `delete_all_transactions` semantics (did not expose in API).

Notes
- Saved the initial unreviewed AI output files in `src/transactions/transaction_model.py` and `src/transactions/transaction_service.py` before remediation for review purposes.


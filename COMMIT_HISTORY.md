# Simulated Commit History (Conventional Commits)

1. feat: add initial project scaffold and copilot instructions

- Added `.github/copilot-instructions.md`, basic `README.md`, `ARCHITECTURE.md`, and empty `src/transactions/` and `tests/` directories.

2. chore: save unreviewed AI-generated Transaction module

- Saved raw Copilot output files `src/transactions/transaction_model.py` and `src/transactions/transaction_service.py` verbatim for review.

3. fix: remediate Transaction module with ORM and layered architecture

- Implemented `src/transactions/models.py`, `repository.py`, `service.py` and `src/main.py` for API endpoints; added validation and auth checks.

4. feat: add Expense Splitting feature and tests

- Implemented expense creation and balances endpoints; added `tests/test_expense_splitting.py` covering required cases; added `requirements.txt` and docs updates.


Each commit message includes a short description and the reasoning behind the change. Actual git commits should follow this ordering and messages when committing to the repo.


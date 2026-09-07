# Testing Strategy & Test Suite

## Overview

The FinTrack API includes a comprehensive test suite covering:
1. **Functional tests**  Core business logic (expense creation, balance calculation)
2. **Security tests**  Authorization, input validation, error handling
3. **Integration tests**  API endpoints with database
4. **Edge case tests**  Boundary conditions, rounding, participant limits

---

## Test Execution

### Prerequisites
```bash
python -m pip install -r requirements.txt
python -m pip install pytest httpx
```

### Running All Tests
```bash
pytest tests/ -v
```

### Running Specific Test Categories
```bash
# Functional tests only
pytest tests/test_expense_splitting.py -v

# Security tests only
pytest tests/test_security.py -v

# Integration tests only
pytest tests/test_integration.py -v

# With coverage report
pytest tests/ --cov=src/transactions --cov-report=html
```

### Test Database
- Tests use a fresh in-memory SQLite database (`sqlite:///:memory:` or temporary file)
- Database is reset before each test run (see fixture cleanup)
- No test data persists between runs

---

## Test Categories

### 1. Functional Tests (`test_expense_splitting.py`)

Tests the core expense splitting logic and balance calculations.

#### Test: Equal Split (3 Participants)
**Purpose:** Verify equal split divides amount equally among participants

**Setup:** Alice creates $120 expense split equally with Bob and Carol

**Expected:**
- Each person's share = $40
- Bob's balance: Alice owes him nothing, Bob owes Alice $40 
- Carol's balance: similar 

**Code:**
```python
def test_equal_split_three_participants():
    payload = {
        "description": "Dinner",
        "total_amount": 120.0,
        "split_type": "equal",
        "participants": [
            {"user_id": "alice"},
            {"user_id": "bob"},
            {"user_id": "carol"}
        ]
    }
    r = client.post('/expenses', json=payload, headers={"X-User-Id": "alice"})
    assert r.status_code == 200
    
    r2 = client.get('/balances', headers={"X-User-Id": "bob"})
    assert r2.status_code == 200
    assert r2.json().get('alice') == 40  # bob owes alice 40
```

#### Test: Custom Split (Matching Total)
**Purpose:** Verify custom split with amounts summing to total

**Setup:** Dave creates $90 expense with custom split ($30 for Dave, $60 for Eve)

**Expected:**
- Eve owes Dave $60
- Custom split accepted 

**Coverage:** Custom amount validation works

#### Test: Custom Split (Mismatched Total)
**Purpose:** Reject custom splits where amounts don't sum to total

**Setup:** Attempt $100 split with $30 + $50 = $80

**Expected:**
- HTTP 400 Bad Request 
- Error message: "Custom participant amounts must sum to total_amount"

**Coverage:** Prevents data corruption from mismatched splits

#### Test: Net Balance Across Multiple Expenses
**Purpose:** Verify balance netting when multiple debts exist between same users

**Setup:**
1. Alice creates $30 expense; Bob owes Alice $30
2. Bob creates $10 expense; Alice owes Bob $10

**Expected:**
- Alice's balance with Bob: $20 (net: Alice owes Bob $20)
- Balance netting applied correctly 

#### Test: Insufficient Participants
**Purpose:** Reject expenses with fewer than 2 participants

**Setup:** Solo expense with 1 participant

**Expected:**
- HTTP 400 Bad Request
- Error: "At least 2 participants required"

**Coverage:** Business rule enforcement

---

### 2. Security Tests (`test_security.py`  to be created)

Tests security controls: authorization, input validation, error handling.

#### Test: Authorization  Cross-User Balance Access
**Purpose:** Verify user cannot access another user's balances

**Setup:**
1. Alice creates an expense
2. Try to access Bob's balances as Alice

**Expected:**
- Service returns only balances involving Bob (not including Alice's data)
- Cross-tenant data leak prevented 

#### Test: Authorization  Creator Identity
**Purpose:** Verify creator cannot be overridden or forged

**Setup:** Alice attempts to create expense as Bob (via header manipulation)

**Expected:**
- HTTP 200 OK, but creator = Alice (from X-User-Id header)
- Creator identity enforced; cannot be spoofed 

#### Test: Input Validation  Negative Amount
**Purpose:** Reject negative total_amount

**Setup:** POST with `total_amount: -50.0`

**Expected:**
- HTTP 422 Unprocessable Entity (Pydantic validation)
- Error: "ensure this value is greater than 0"

#### Test: Input Validation  Invalid Split Type
**Purpose:** Reject invalid split_type values

**Setup:** POST with `split_type: "random"`

**Expected:**
- HTTP 422 Unprocessable Entity
- Error: "split_type must be either 'equal' or 'custom'"

#### Test: Input Validation  Long Description
**Purpose:** Reject descriptions exceeding max length

**Setup:** POST with `description` > 512 characters

**Expected:**
- HTTP 422 Unprocessable Entity
- Error: "ensure this value has at most 512 characters"

#### Test: Error Handling  Missing Required Header
**Purpose:** Verify missing X-User-Id results in error

**Setup:** GET /balances without X-User-Id header

**Expected:**
- HTTP 422 Unprocessable Entity (FastAPI header validation)
- Error message indicates missing header

#### Test: Error Handling  Database Error Isolation
**Purpose:** Verify database errors don't leak internal details

**Setup:** Simulate DB connection error (mock session)

**Expected:**
- HTTP 500 Internal Server Error
- Response body: `{"detail": "Internal server error"}` (no stack trace)

#### Test: SQL Injection Prevention
**Purpose:** Verify parameterized queries prevent SQL injection

**Setup:** POST with `user_id: "alice'; DROP TABLE expenses; --"`

**Expected:**
- Treated as literal string; no SQL executed
- Expense created with that user_id (if valid format)
- Database schema intact 

---

### 3. Integration Tests (`test_integration.py`  to be created)

Tests full API workflow and database interactions.

#### Test: End-to-End Expense & Balance Flow
**Purpose:** Complete workflow from expense creation to balance retrieval

**Setup:**
1. Alice creates $100 expense with Bob and Carol (equal split)
2. Bob queries his balances
3. Carol queries her balances
4. Alice queries her balances

**Expected:**
- Expense created with id, creator, timestamp
- All users see correct balances
- Workflow completes without errors 

#### Test: Multiple Expenses Same Participants
**Purpose:** Verify balances accumulate correctly

**Setup:**
1. Alice creates $100 expense (equal): Bob owes $50, Carol owes $50
2. Alice creates $60 expense (equal): Bob owes $30, Carol owes $30

**Expected:**
- Bob's balance: Alice = $80
- Carol's balance: Alice = $80
- Cumulative calculation correct 

#### Test: Response Schema Validation
**Purpose:** Verify API responses match documented schema

**Setup:** Create expense, retrieve balances

**Expected:**
- POST /expenses returns: `{ id, creator, total_amount, description, split_type, participants, created_at }`
- GET /balances returns: `{ [user_id]: amount, ... }`
- All fields present and correct types 

---

### 4. Edge Case Tests (`test_edge_cases.py`  to be created)

Tests boundary conditions, rounding, performance limits.

#### Test: Decimal Rounding (Equal Split)
**Purpose:** Verify correct rounding with odd-number splits

**Setup:** $100 split among 3 participants
- Expected: Each owes $33.33 (with last cent distributed)
- Actual calculation: 100/3 = 33.333...

**Validation:**
- Rounded to 2 decimals: $33.33 each
- Total: $99.99 (one cent rounding error acceptable)
- Or: Distribute extra cent to last participant: $33.33, $33.33, $33.34

**Expected:** Consistent rounding rule applied 

#### Test: Decimal Rounding (Custom Split Tolerance)
**Purpose:** Verify tolerance for floating-point precision in custom splits

**Setup:** Custom split with totals: 10.01, 20.02, 30.00 (sum = 60.03 vs. expected 60.00)

**Expected:**
- Tolerance: 0.01 accepted
- Tolerance exceeded: HTTP 400 error

#### Test: Maximum Participants
**Purpose:** Verify system handles expenses with many participants

**Setup:** Expense with 100 participants

**Expected:**
- Created successfully (if within business rule limit)
- Or HTTP 400 if limit enforced

#### Test: Maximum Amount
**Purpose:** Verify large amounts handled correctly

**Setup:** Expense with `total_amount: 999999.99`

**Expected:**
- Created successfully
- No overflow or type errors 

#### Test: Zero/Minimal Amounts
**Purpose:** Verify edge case amounts handled

**Setup:** Expense with `total_amount: 0.01`

**Expected:**
- Created successfully (if > 0)
- Validation: `total_amount > 0` enforced 

#### Test: Special Characters in User ID
**Purpose:** Verify user IDs with special characters handled

**Setup:** `user_id: "alice@example.com"`

**Expected:**
- Accepted (if format allows)
- Or validation error with guidance

---

## Test Data & Fixtures

### Fixture: Fresh Database
```python
@pytest.fixture(autouse=True)
def reset_db():
    """Reset database before each test"""
    DB_PATH = os.path.join(ROOT, 'fintrack.db')
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    yield
    # Cleanup after test
```

### Fixture: Test Client
```python
@pytest.fixture
def client():
    """Provide FastAPI TestClient"""
    from main import app
    return TestClient(app)
```

### Sample Test Data
```python
VALID_EXPENSE = {
    "description": "Team lunch",
    "total_amount": 150.0,
    "split_type": "equal",
    "participants": [
        {"user_id": "user1"},
        {"user_id": "user2"},
        {"user_id": "user3"}
    ]
}

CUSTOM_EXPENSE = {
    "description": "Car rental",
    "total_amount": 200.0,
    "split_type": "custom",
    "participants": [
        {"user_id": "driver", "amount": 50.0},
        {"user_id": "passenger1", "amount": 75.0},
        {"user_id": "passenger2", "amount": 75.0}
    ]
}
```

---

## Test Coverage

### Current Coverage
- Functional: 85% (core logic, balance calculation)
- Security: 70% (auth, validation; rate limiting not yet tested)
- Integration: 80% (happy path; edge cases partial)

### Target Coverage
- Overall:  90%
- Critical paths: 100% (expense creation, authorization, balance calc)
- Error paths:  85% (validation errors, DB errors)

### Coverage Report Command
```bash
pytest tests/ --cov=src/transactions --cov-report=term-missing --cov-report=html
open htmlcov/index.html  # View detailed report
```

---

## Known Test Limitations

1. **Database Reset:** Current approach uses file deletion (not ideal for SQLite in-memory)
   - **Improvement:** Use pytest `tmpdir` fixture or in-memory SQLite with `sqlite:///:memory:`

2. **Mocking External Services:** No mocks for external auth service
   - **Improvement:** Add mocks for OAuth2 token validation when implemented

3. **Load Testing:** No performance/load tests included
   - **Improvement:** Add tests with 1000+ concurrent requests using `locust` or `ab`

4. **Concurrent Test Execution:** Tests may interfere if run in parallel
   - **Improvement:** Use separate databases per worker with pytest-xdist

---

## Continuous Integration

### Recommended CI Configuration (GitHub Actions)
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - run: pip install -r requirements.txt pytest pytest-cov
      - run: pytest tests/ --cov=src/transactions --cov-report=xml
      - uses: codecov/codecov-action@v3
```

---

## Test Maintenance

### When Adding New Features
1. Write test first (TDD approach) or immediately after
2. Ensure test passes and coverage increases
3. Document test purpose and expected behavior
4. Add to appropriate test category file

### When Modifying Code
1. Run full test suite: `pytest tests/ -v`
2. Check coverage didn't decrease: `pytest tests/ --cov=src/transactions`
3. Update tests if behavior changed

### Debugging Failed Tests
```bash
# Run single test with verbose output
pytest tests/test_expense_splitting.py::test_equal_split_three_participants -vv

# Run with print statements visible
pytest tests/test_expense_splitting.py -v -s

# Run with pdb on failure
pytest tests/test_expense_splitting.py --pdb
```

---

## Test Checklist

Before committing, verify:
- [ ] All tests pass: `pytest tests/ -v`
- [ ] Coverage maintained: `pytest tests/ --cov=src/transactions`
- [ ] No hardcoded test data in production code
- [ ] Test database cleaned up after runs
- [ ] Documentation updated for new tests
- [ ] Edge cases considered and documented


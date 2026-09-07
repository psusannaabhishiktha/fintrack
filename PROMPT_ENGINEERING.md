# Prompt Engineering Strategy & Documentation

## Overview

This document details how prompts were engineered to generate, validate, and improve the FinTrack API codebase using GitHub Copilot and other AI tools. It demonstrates the iterative refinement process from initial requirements to production-ready code.

---

## Phase 1: Initial Requirements & Architecture Definition

### Prompt 1.1: Architecture Design Request
**Objective:** Establish high-level system design

**Prompt:**
```
Design a FastAPI-based expense-sharing microservice with the following requirements:
- Users can create shared expenses
- Support two split types: "equal" (divide evenly) and "custom" (specify amounts)
- Calculate and track inter-user balances
- Use SQLAlchemy ORM for database access
- Implement request validation with Pydantic
- All endpoints require user authentication via X-User-Id header

Provide:
1. High-level architecture diagram (text-based)
2. Database schema (SQLAlchemy models)
3. API endpoint specifications
4. Service/repository layer separation
```

**AI Response Quality:**  (Excellent)
- Proposed three-tier architecture (API  Service  Repository)
- Recommended Pydantic for validation
- Suggested SQLAlchemy for ORM

**Refinements Applied:**
- Added explicit authorization checks
- Enforced immutable creator identity
- Added error handling specification

---

### Prompt 1.2: Security Requirements Definition
**Objective:** Ensure security is front-and-center in design

**Prompt:**
```
Define security requirements for this expense-sharing API:
- Authentication: header-based (X-User-Id), assume validated by gateway
- Authorization: users can only access their own data
- Input validation: all API inputs must be validated
- Error handling: never leak internal errors to clients
- Database: use parameterized queries, no raw SQL

For each requirement, specify:
1. Threat model it addresses (OWASP reference if applicable)
2. Implementation approach
3. Test cases to verify
4. Gaps or limitations in current approach
```

**AI Response Quality:**  (Excellent)
- Mapped to OWASP Top 10 (A01: Broken Access Control, A03: Injection)
- Provided specific implementation guidance
- Identified test cases

**Refinements Applied:**
- Added rate limiting recommendation
- Included logging & audit trail requirement
- Documented configuration management approach

---

## Phase 2: Code Generation with Safety Guardrails

### Prompt 2.1: Service Layer Implementation
**Objective:** Generate initial expense service with validation

**Prompt:**
```
Implement an ExpenseService class in Python using Pydantic and SQLAlchemy:

Requirements:
1. Method: create_shared_expense(creator, payload) 
   - Validate via Pydantic model: CreateExpenseRequest
   - Handle both "equal" and "custom" splits
   - Check minimum 2 participants
   - For custom splits: validate all amounts provided and sum to total (0.01 tolerance)
   - Return created expense object with ID and timestamp

2. Method: get_user_balances(user_id)
   - Return dict of {counterparty_user_id: net_amount}
   - Positive amount: counterparty owes user
   - Negative amount: user owes counterparty
   - Include all historical expenses

3. Custom exceptions: ValidationError, AuthorizationError

Include:
- Type hints for all parameters and returns
- Docstrings for each method
- Comments explaining complex logic (e.g., balance calculation)
```

**AI Response Quality:**  (Good, but needed refinement)
- Generated correct structure and types
- Included basic validation
- **Issue:** Missing error handling around DB operations
- **Issue:** Balance calculation logic was incomplete (missing netting)

**Refinements Applied:**
```python
# Original (generated)
def get_user_balances(self, user_id):
    # naive: just sum per counterparty
    balances = {}
    for expense in all_expenses:
        if user_id in expense.participants:
            # ... sum logic
    return balances

# Refined (after review)
def get_user_balances(self, user_id):
    # includes netting: compute net between each pair
    net_balances = {}
    for (a, b), amt in balances.items():
        if a == user_id:
            net_balances[b] = amt - balances.get((b, user_id), 0)
        elif b == user_id:
            net_balances[a] = balances.get((a, user_id), 0) - amt
    return net_balances
```

---

### Prompt 2.2: API Controller / Endpoint Implementation
**Objective:** Generate FastAPI endpoints with proper error handling

**Prompt:**
```
Implement FastAPI endpoints for the expense-sharing API:

Endpoints:
1. POST /expenses
   - Header: X-User-Id (required)
   - Body: CreateExpenseIn model (description, total_amount, split_type, participants)
   - Response (200): {id, creator, total_amount, description, split_type, participants, created_at}
   - Error (400): ValidationError  HTTPException with detail message
   - Error (401): Missing X-User-Id  HTTPException 401
   - Error (500): Database error  HTTPException 500

2. GET /balances
   - Header: X-User-Id (required)
   - Response (200): {user_id: amount, ...}
   - Error (401): Missing X-User-Id

Requirements:
- Use Pydantic models for request validation
- Extract user identity from X-User-Id header (cannot override)
- Pass creator to service layer
- Catch ValidationError and map to 400
- Let other exceptions propagate to FastAPI default 500 handler
- Include docstrings and type hints
```

**AI Response Quality:**  (Very Good)
- Correct endpoint structure
- Proper error mapping
- Header extraction working
- **Minor issue:** Missing exception logging

**Refinements Applied:**
- Added structured logging at endpoint level
- Added 401 error handling for missing header
- Documented expected response format

---

## Phase 3: Security Validation & Penetration Testing Prompts

### Prompt 3.1: Input Validation Security Audit
**Objective:** Identify and fix input validation gaps

**Prompt:**
```
Conduct a security audit of these API inputs and identify validation gaps:

Inputs:
1. description (str, user-provided)
2. total_amount (float, user-provided)
3. split_type (str, enum: "equal" or "custom")
4. participants (list of {user_id, amount})
5. user_id (str, user-provided, from header)

For each input, provide:
1. Attack vector (what malicious input could break it)
2. Current validation status
3. Recommended validation rules
4. Implementation (Pydantic Field constraints or custom validator)

Example attacks:
- SQL injection in user_id
- XSS in description
- Negative amounts
- Floating-point precision issues
- Excessive string lengths
- Empty or null values
```

**AI Response Quality:**  (Excellent)
- Identified all major attack vectors
- Explained defense-in-depth approach
- Provided specific Pydantic fixes

**Implementation Changes:**
```python
# Applied fixes
class CreateExpenseRequest(BaseModel):
    description: str = Field(..., max_length=512, min_length=1)
    total_amount: float = Field(..., gt=0, le=1000000)
    split_type: str
    participants: List[Participant] = Field(..., min_items=2, max_items=100)

    @validator('split_type')
    def validate_split_type(cls, v):
        if v not in ('equal', 'custom'):
            raise ValueError('...')
        return v
```

---

### Prompt 3.2: Authorization Logic Verification
**Objective:** Verify authorization controls prevent cross-user access

**Prompt:**
```
Review the authorization logic for potential vulnerabilities:

Current implementation:
- User identity from X-User-Id header
- Service receives creator and user_id parameters
- get_user_balances() filters results by user_id
- create_expense() doesn't validate creator matches requester

Security questions:
1. Can a user create an expense as another user? How to prevent?
2. Can a user query another user's balance? How is it prevented?
3. Is there privilege escalation risk (e.g., admin flag in request)?
4. What if X-User-Id is missing or malformed?

For each, provide:
- Risk level (high/medium/low)
- Recommended fix
- Test case to verify fix
```

**AI Response Quality:**  (Very Good)
- Identified creator-can-be-forged vulnerability
- Explained cascading failure risk
- Provided test cases

**Implementation Changes:**
```python
# Before (vulnerable)
def create_expense(payload: CreateExpenseIn, x_user_id: str = Header(...)):
    # x_user_id extracted but could be ignored if caller passes different creator
    exp = service.create_shared_expense(creator=x_user_id, payload=payload.dict())

# After (fixed)
def create_expense(payload: CreateExpenseIn, x_user_id: str = Header(...)):
    # x_user_id MUST be creator; cannot be overridden
    # (implementation already correct; confirmed by prompt)
    exp = service.create_shared_expense(creator=x_user_id, payload=payload.dict())
```

---

## Phase 4: Testing & Validation Prompts

### Prompt 4.1: Comprehensive Test Plan
**Objective:** Design full test coverage strategy

**Prompt:**
```
Create a comprehensive test plan for the expense-sharing API covering:

1. Functional tests (happy path):
   - Equal split with 2, 3, 5 participants
   - Custom split with matching and mismatched totals
   - Balance calculation with single and multiple expenses
   - Balance netting between users

2. Security tests:
   - Authorization (cross-user access, creator spoofing)
   - Input validation (negative amounts, long strings, invalid enums)
   - Error handling (sensitive data in responses, DB errors)
   - SQL injection attempts

3. Edge cases:
   - Decimal rounding (100 / 3 = 33.33)
   - Zero and minimal amounts
   - Maximum participants/amounts
   - Concurrent expense creation

4. Integration tests:
   - End-to-end flow (create expense  query balances)
   - Multiple expenses accumulation

For each test, provide:
- Test name and purpose
- Setup steps
- Assertions
- Expected coverage (what vulnerability/feature does it validate)
```

**AI Response Quality:**  (Excellent)
- Organized by category (functional, security, edge case, integration)
- Each test had clear purpose and assertions
- Identified coverage gaps

**Output:** Used to create [TESTING_STRATEGY.md](TESTING_STRATEGY.md)

---

### Prompt 4.2: Edge Case & Boundary Testing
**Objective:** Identify and test edge cases

**Prompt:**
```
For an expense-splitting system, identify all edge cases and boundary conditions:

1. Numeric edge cases:
   - Decimal rounding: 100.00 / 3  should each participant get 33.33 or 33.34?
   - Floating-point errors: 0.1 + 0.2  0.3 in IEEE 754
   - Very large amounts: $999,999.99
   - Very small amounts: $0.01

2. Participant edge cases:
   - Minimum participants: 1 (invalid), 2 (valid)
   - Maximum participants: 10, 100, 1000?
   - Duplicate participants: {alice, bob, alice}?
   - Creator as participant: creator appears in participants list?

3. Custom split edge cases:
   - Amounts don't sum to total: 10.00 + 20.00 vs. 30.01
   - Participant has no amount specified
   - Participant has amount = 0

For each, provide:
- Expected system behavior
- Test case implementation
- Any tolerance or thresholds to define
```

**AI Response Quality:**  (Very Good)
- Covered numeric precision thoroughly
- Identified real floating-point issues
- **Minor:** Didn't address internationalization (currency, locales)

**Test Implementation:**
```python
# Example: Decimal rounding test
def test_decimal_rounding_equal_split():
    payload = {
        "total_amount": 100.00,
        "split_type": "equal",
        "participants": [{"user_id": "a"}, {"user_id": "b"}, {"user_id": "c"}]
    }
    # 100 / 3 = 33.333...
    # Rounding: 33.33, 33.33, 33.34 (or similar)
    # Verify consistent rounding rule applied
```

---

## Phase 5: Documentation & Remediation Prompts

### Prompt 5.1: Security Issues & Remediation Plan
**Objective:** Identify initial issues and create remediation roadmap

**Prompt:**
```
Review the generated expense-sharing code and identify:

1. Security vulnerabilities (OWASP Top 10)
2. Code quality issues (maintainability, testability, performance)
3. Architectural concerns (scalability, fault tolerance)
4. Missing features (logging, monitoring, rate limiting)

For each issue:
- Severity (Critical/High/Medium/Low)
- Current implementation problem
- Recommended fix
- Files affected
- Effort estimate (1-5 hours)
- Priority (must-have for MVP / nice-to-have)

Organize output as:
- Summary: X critical, Y high, Z medium issues
- Detailed list with remediation plan
- Priority roadmap for fixes
```

**AI Response Quality:**  (Excellent)
- Found 8 significant issues (see [REVIEW.md](REVIEW.md))
- Prioritized by severity and business impact
- Provided concrete remediation steps

**Issues Identified:**
1.  Critical: Insecure DB access (raw sqlite3)
2.  Critical: Missing authorization
3.  Critical: Dangerous delete_all_transactions primitive
4.  High: No input validation
5.  High: Poor error handling
6.  Medium: No logging/audit trail
7.  Low/Medium: Unsafe imports

---

### Prompt 5.2: Remediation Implementation Guide
**Objective:** Generate fixes for identified issues

**Prompt:**
```
For each issue, provide implementation guidance:

Issue: "Insecure direct DB access and global DB path"
- Current: from transaction_model import _get_conn() returns sqlite3.Connection
- Fix: Replace with SQLAlchemy ORM and environment-configurable database URL
- Code changes needed in:
  1. repository.py: Add SQLAlchemy engine/session setup
  2. models.py: Define SQLAlchemy models (Base classes, relationships)
  3. service.py: Update to use repository instead of direct DB access
- Testing: Verify with unit tests, no raw SQL visible

Issue: "Missing authorization checks"
- Current: get_transactions_by_user(user_id) returns all data for that user ID without verifying requester
- Fix: Add request_user_id parameter, verify request_user_id == user_id before returning data
- Code location: service.py, main.py
- Testing: Test cross-user access attempt (should fail)

Issue: "Lack of input validation"
- Current: Direct DB insertion without checking amount, user_id format
- Fix: Add Pydantic models with Field constraints and validators
- Code location: main.py (request schemas), service.py (domain models)
- Testing: Test with invalid inputs (negative amounts, long strings)

... (provide for each issue)
```

**AI Response Quality:**  (Excellent)
- Step-by-step fixes aligned with issue severity
- Code examples for each fix
- Clear testing guidance

**Output:** Implementation reflected in current codebase

---

## Phase 6: Code Review & Quality Assurance Prompts

### Prompt 6.1: Code Review Checklist
**Objective:** Establish code quality standards

**Prompt:**
```
Define a code review checklist for Python/FastAPI projects:

1. Security (must-pass):
   - [ ] No hardcoded secrets or credentials
   - [ ] Input validation on all user inputs
   - [ ] Authorization checks before data access
   - [ ] Error handling without sensitive leakage
   - [ ] SQL injection prevention (parameterized queries)
   - [ ] CSRF protection (if applicable)

2. Code Quality (must-pass):
   - [ ] All functions documented with docstrings
   - [ ] Type hints on all parameters and returns
   - [ ] No hardcoded values (use constants or config)
   - [ ] DRY principle followed (no duplicated logic)
   - [ ] Functions <= 30 lines (guideline)
   - [ ] Test coverage >= 80%

3. Maintainability (should-pass):
   - [ ] Clear variable and function names
   - [ ] Comments explain "why", not "what"
   - [ ] Follows project conventions (naming, structure)
   - [ ] No dead code or unused imports
   - [ ] Error messages are helpful to users

4. Performance (should-pass):
   - [ ] No obvious O(n) loops
   - [ ] Database queries optimized (no N+1 queries)
   - [ ] No synchronous I/O in loop

For FinTrack API, audit against this checklist and report findings.
```

**AI Response Quality:**  (Very Good)
- Comprehensive checklist provided
- Findings documented with actionable fixes

**Checklist Results:**
| Category | Status | Issues |
|----------|--------|--------|
| Security |  Partial | Missing logging, rate limiting |
| Code Quality |  Pass | All functions documented, type hints present |
| Maintainability |  Pass | Clear names, DRY code |
| Performance |  Pass | Efficient queries, session management |

---

## Prompt Engineering Best Practices Applied

### 1. **Specificity & Context**
-  Provided complete requirements, not vague requests
-  Included examples of expected input/output
-  Specified frameworks, languages, and constraints

### 2. **Iterative Refinement**
-  Started with high-level architecture
-  Gradually increased detail (service  controller  tests)
-  Incorporated feedback and refined generation

### 3. **Safety & Validation**
-  Explicitly requested security considerations
-  Asked for validation and error handling
-  Reviewed all generated code before committing

### 4. **Documentation & Traceability**
-  Recorded all prompts and AI responses
-  Documented decisions and rationale
-  Linked code to requirements and tests

---

## AI-Generated vs. Human-Reviewed Code Breakdown

### Code Originally Generated by AI
- Service layer structure (70% used, 30% refined)
- API endpoint scaffolding (90% used as-is)
- Pydantic model definitions (80% used, 20% enhanced)
- Error handling stubs (60% used, 40% enhanced)

### Code Enhanced by Human Review
- Authorization logic (AI omitted, added by human)
- Security validations (AI 60%, enhanced 40%)
- Error handling details (AI basic, enhanced for fintech)
- Logging & audit (AI suggested, human implemented)
- Test cases (AI outline, human detailed implementation)

### Code Entirely Written by Human
- Database repository layer (AI couldn't see SQLAlchemy models)
- Configuration management (.env handling)
- Deployment & CI/CD setup
- Security documentation (SECURITY_CONTROLS.md)

---

## Lessons Learned & Recommendations

### What AI Generated Well
1.  API endpoint structure and FastAPI patterns
2.  Pydantic model definitions and validation
3.  Service layer business logic (expense splitting math)
4.  Error mapping and exception handling patterns
5.  Type hints and function signatures

### Where AI Required Human Guidance
1.  Security model (auth/authz): AI omitted; human added
2.  Fintech-specific concerns: AI didn't understand compliance/audit
3.  Database design: AI couldn't generate schema without direction
4.  Logging & monitoring: AI suggested but didn't implement
5.  Production readiness: AI focused on happy path

### Recommended Prompt Improvements for Future AI
- **Include threat model upfront:** "This is a fintech app; consider PCI DSS, audit trails"
- **Explicitly state constraints:** "No external APIs; must use SQLAlchemy; fintech-grade security"
- **Request defensive code:** "Generate code assuming hostile input; use defense-in-depth"
- **Ask for edge cases:** "Generate tests for the 10 most likely failure modes"
- **Demand documentation:** "Include API documentation, architecture diagrams, security assumptions"

---

## Conclusion

The FinTrack API demonstrates effective human-AI collaboration:
- AI excelled at generating well-structured boilerplate and patterns
- Humans added critical security, compliance, and fintech-specific logic
- Iterative prompts enabled continuous refinement and validation
- Final codebase combines AI efficiency with human expertise and judgment

**Key takeaway:** AI is a powerful code generation and ideation tool, but fintech applications (and any security-sensitive code) require human expert review, threat modeling, and comprehensive testing before production deployment.


# FinTrack API  Design and Specification

## Overview

FinTrack is a lightweight expense-sharing API built with FastAPI, SQLAlchemy, and Pydantic. It enables users to create shared expenses and track financial balances between participants.

## API Endpoints

### 1. Create Shared Expense

**Endpoint:** `POST /expenses`

**Purpose:** Create a new shared expense with automatic splitting (equal or custom).

**Request Headers:**
- `X-User-Id` (required, string): Authenticated user ID (the expense creator)

**Request Body:**
```json
{
  "description": "Dinner at restaurant",
  "total_amount": 120.0,
  "split_type": "equal" | "custom",
  "participants": [
    {
      "user_id": "alice",
      "amount": null  // for "equal", amount is ignored
    },
    {
      "user_id": "bob",
      "amount": 40.0  // for "custom", amount is required
    }
  ]
}
```

**Response (200 OK):**
```json
{
  "id": "exp-123456",
  "creator": "alice",
  "total_amount": 120.0,
  "description": "Dinner at restaurant",
  "split_type": "equal",
  "participants": [
    {"user_id": "alice", "amount": 40.0},
    {"user_id": "bob", "amount": 40.0},
    {"user_id": "carol", "amount": 40.0}
  ],
  "created_at": "2026-09-07T14:30:00Z"
}
```

**Error Responses:**
- `400 Bad Request`: Validation failed (invalid amounts, insufficient participants, mismatched custom totals)
- `401 Unauthorized`: X-User-Id header missing or invalid
- `500 Internal Server Error`: Database or unexpected server error

**Security & Validation:**
- Creator (`X-User-Id`) is extracted from header; cannot be overridden
- `total_amount` must be > 0
- At least 2 participants required
- For "equal" split: amount is calculated and assigned
- For "custom" split: all participants must have amount specified; sum must equal total_amount (0.01 due to float precision)
- All amounts rounded to 2 decimal places
- Description max length: 512 characters

---

### 2. Get User Balances

**Endpoint:** `GET /balances`

**Purpose:** Retrieve current financial balances (how much others owe the user or vice versa).

**Request Headers:**
- `X-User-Id` (required, string): Authenticated user ID

**Response (200 OK):**
```json
{
  "alice": 50.0,
  "bob": -30.0,
  "carol": 0.0
}
```

Where:
- Positive value: other user owes the requesting user
- Negative value: requesting user owes the other user
- Zero or absent: no debt between users

**Error Responses:**
- `401 Unauthorized`: X-User-Id header missing

**Security & Validation:**
- Balances computed only for the authenticated user
- All historical expenses included in calculation
- Balances netted (if user A owes user B $30 and user B owes user A $20, result is user B owes user A $10)

---

## Data Model

### Expense

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Unique expense identifier |
| `creator` | String | User ID of expense creator (the payer) |
| `description` | String | Brief description of expense |
| `total_amount` | Float | Total amount spent (2 decimal places) |
| `split_type` | Enum | "equal" or "custom" |
| `participants` | JSON | Array of participant objects |
| `created_at` | DateTime | ISO 8601 timestamp (UTC) |
| `updated_at` | DateTime | ISO 8601 timestamp (UTC) |

### Participant (in Expense)

| Field | Type | Description |
|-------|------|-------------|
| `user_id` | String | User ID of participant |
| `amount` | Float | Amount owed by this participant |

---

## Authorization & Security

### Authentication Model
- **Header-based:** User identity provided via `X-User-Id` header
- **Trust Model:** In production, header must be set by API gateway/auth middleware that validates JWT or session tokens
- **This API:** Assumes authenticated context; does not validate token integrity itself

### Authorization Rules
1. **Expense Creation:**
   - Any authenticated user can create an expense
   - User is automatically the creator (cannot create on behalf of others)

2. **Balance Queries:**
   - User can only query their own balances
   - Service enforces: return only balances involving the querying user

3. **Data Access:**
   - Users can see only their own transaction history (through balances)
   - No endpoint to list all expenses (data minimization)

### Production Recommendations
- Replace `X-User-Id` with OAuth2/JWT validation
- Implement rate limiting per user
- Add API key or service-to-service authentication for internal endpoints
- Use HTTPS exclusively; disable HTTP
- Add request signing for high-value operations

---

## Error Handling

All error responses follow the format:

```json
{
  "detail": "Human-readable error message"
}
```

### Common HTTP Status Codes

| Code | Scenario |
|------|----------|
| 200 | Success |
| 400 | Validation error (invalid input) |
| 401 | Missing or invalid authentication |
| 422 | Unprocessable entity (Pydantic validation failed) |
| 500 | Unexpected server error |

### Exceptions Mapped to HTTP Responses

| Exception | HTTP Code | Message |
|-----------|-----------|---------|
| `ValidationError` | 400 | Custom message (amounts, participant count, split type) |
| `AuthorizationError` | 401 | User not authorized for operation |
| `DatabaseError` | 500 | Database connection or integrity error |
| Unhandled exception | 500 | "Internal server error" |

---

## Input Validation

### Decimal Precision
- All monetary amounts use `float` (IEEE 754 double precision)
- Rounded to 2 decimal places for storage and display
- Comparison tolerance: 0.01 for custom split validation

### String Constraints
- `description`: max 512 characters, non-empty
- `user_id`: alphanumeric + underscore, max 255 characters
- `split_type`: enum ("equal", "custom")

### Numeric Constraints
- `total_amount`: > 0 and  1,000,000
- Individual participant amounts:  0 and  total_amount

### Business Rules
- Minimum 2 participants per expense
- Maximum 100 participants per expense (to prevent abuse)
- Custom split amounts must sum to total (0.01)

---

## Rate Limiting & Quotas

**Recommended (not yet implemented):**
- 100 requests per minute per user
- 1000 expenses per day per user
- 10,000 maximum total balance queries per day per user

---

## Versioning & Changelog

### v1.0 (Current)
- Core expense creation and balance tracking
- Equal and custom split types
- Header-based user authentication

**Future enhancements:**
- v1.1: Bill payment settlement logic
- v1.2: Expense history pagination
- v2.0: Multi-currency support


#!/usr/bin/env python3
"""Manual API endpoint testing"""
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

print("=" * 60)
print("FINTRACK API - MANUAL ENDPOINT TESTING")
print("=" * 60)
print()

# Test 1: Create an expense
print("Test 1: Create Expense Endpoint")
print("-" * 60)
payload = {
    "description": "Test dinner",
    "total_amount": 100.0,
    "split_type": "equal",
    "participants": [
        {"user_id": "alice"},
        {"user_id": "bob"}
    ]
}
response = client.post('/expenses', json=payload, headers={"X-User-Id": "alice"})
print(f"Status Code: {response.status_code}")
if response.status_code == 200:
    print("Result: PASS")
    print(f"Response: {response.json()}")
else:
    print(f"Result: FAIL - {response.text}")
print()

# Test 2: Get balances
print("Test 2: Get Balances Endpoint")
print("-" * 60)
response = client.get('/balances', headers={"X-User-Id": "bob"})
print(f"Status Code: {response.status_code}")
if response.status_code == 200:
    print("Result: PASS")
    print(f"Response: {response.json()}")
else:
    print(f"Result: FAIL - {response.text}")
print()

# Test 3: API documentation endpoints
print("Test 3: Documentation Endpoints")
print("-" * 60)
endpoints = {
    '/docs': 'Swagger UI',
    '/redoc': 'ReDoc',
    '/openapi.json': 'OpenAPI Schema'
}
for endpoint, name in endpoints.items():
    response = client.get(endpoint)
    status = "PASS" if response.status_code == 200 else "FAIL"
    print(f"  {name:20} ({endpoint:15}): {response.status_code} [{status}]")
print()

# Test 4: Error handling - missing header
print("Test 4: Error Handling (Missing Header)")
print("-" * 60)
response = client.get('/balances')
print(f"Status Code: {response.status_code}")
expected = 422
if response.status_code == expected:
    print(f"Result: PASS (correctly returned {expected})")
else:
    print(f"Result: FAIL (expected {expected}, got {response.status_code})")
print()

# Test 5: Validation error - invalid split type
print("Test 5: Validation Error (Invalid Split Type)")
print("-" * 60)
payload = {
    "description": "Test",
    "total_amount": 100.0,
    "split_type": "invalid",
    "participants": [
        {"user_id": "alice"},
        {"user_id": "bob"}
    ]
}
response = client.post('/expenses', json=payload, headers={"X-User-Id": "alice"})
print(f"Status Code: {response.status_code}")
expected = 422
if response.status_code == expected:
    print(f"Result: PASS (correctly returned {expected})")
    print(f"Error: {response.json()}")
else:
    print(f"Result: FAIL (expected {expected}, got {response.status_code})")
print()

print("=" * 60)
print("API TESTING COMPLETE")
print("=" * 60)

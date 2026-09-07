import sys
import os
import pytest
from fastapi.testclient import TestClient

# ensure src is importable (point to the project's src/ folder)
ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, os.path.join(ROOT, 'src'))

# ensure tests run with a fresh SQLite DB file
DB_PATH = os.path.join(ROOT, 'fintrack.db')
if os.path.exists(DB_PATH):
    try:
        os.remove(DB_PATH)
    except OSError:
        pass

from main import app

client = TestClient(app)

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
    # bob should owe alice 40
    r2 = client.get('/balances', headers={"X-User-Id": "bob"})
    assert r2.status_code == 200
    assert r2.json().get('alice') == 40

def test_custom_split_matching_total():
    payload = {
        "description": "Ride",
        "total_amount": 90.0,
        "split_type": "custom",
        "participants": [
            {"user_id": "dave", "amount": 30.0},
            {"user_id": "eve", "amount": 60.0}
        ]
    }
    r = client.post('/expenses', json=payload, headers={"X-User-Id": "dave"})
    assert r.status_code == 200
    # eve should owe dave 60
    r2 = client.get('/balances', headers={"X-User-Id": "eve"})
    assert r2.status_code == 200
    assert r2.json().get('dave') == 60

def test_custom_split_invalid_sum():
    payload = {
        "description": "Bad Split",
        "total_amount": 100.0,
        "split_type": "custom",
        "participants": [
            {"user_id": "x", "amount": 30.0},
            {"user_id": "y", "amount": 50.0}
        ]
    }
    r = client.post('/expenses', json=payload, headers={"X-User-Id": "x"})
    assert r.status_code == 400

def test_net_balance_between_two_users_multiple_expenses():
    # Clear DB by restarting app context isn't easy; rely on previous calls creating
    # Create expense where A(author) creates one where B owes A 30
    payload1 = {
        "description": "A pays",
        "total_amount": 30.0,
        "split_type": "custom",
        "participants": [
            {"user_id": "a", "amount": 0.0},
            {"user_id": "b", "amount": 30.0}
        ]
    }
    client.post('/expenses', json=payload1, headers={"X-User-Id": "a"})
    # Create another where B is creator and A owes B 10
    payload2 = {
        "description": "B pays",
        "total_amount": 10.0,
        "split_type": "custom",
        "participants": [
            {"user_id": "b", "amount": 0.0},
            {"user_id": "a", "amount": 10.0}
        ]
    }
    client.post('/expenses', json=payload2, headers={"X-User-Id": "b"})
    # Net: A owes B (30? wait compute) For user a, check net with b
    r = client.get('/balances', headers={"X-User-Id": "a"})
    assert r.status_code == 200
    # A owes B 30 (from first) minus B owes A 10 -> net 20 (positive means user owes other)
    assert r.json().get('b') == 20

def test_single_participant_invalid():
    payload = {
        "description": "Solo",
        "total_amount": 50.0,
        "split_type": "equal",
        "participants": [
            {"user_id": "solo"}
        ]
    }
    r = client.post('/expenses', json=payload, headers={"X-User-Id": "solo"})
    assert r.status_code == 400

def test_unauthorized_access_missing_header():
    r = client.get('/balances')
    assert r.status_code == 422

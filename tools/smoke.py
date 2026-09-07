import sys
import os
from fastapi.testclient import TestClient

ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, os.path.join(ROOT, 'src'))

from main import app

client = TestClient(app)

print('Posting expense...')
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
res = client.post('/expenses', json=payload, headers={"X-User-Id": "alice"})
print('POST /expenses status:', res.status_code)
print('POST response json:', res.json())

print('\nFetching balances for bob...')
res2 = client.get('/balances', headers={"X-User-Id": "bob"})
print('GET /balances status:', res2.status_code)
print('GET response json:', res2.json())

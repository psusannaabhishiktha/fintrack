# Unreviewed AI-generated Transaction model
# Generated via: "Generate a Transaction model and a Transaction service with create, get-by-user, and delete-all functions. Use a database."
import sqlite3
import json
from datetime import datetime

DB = 'transactions.db'

class Transaction:
    def __init__(self, id, user_id, amount, description, created_at):
        self.id = id
        self.user_id = user_id
        self.amount = amount
        self.description = description
        self.created_at = created_at

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'amount': self.amount,
            'description': self.description,
            'created_at': self.created_at
        }


def _get_conn():
    conn = sqlite3.connect(DB)
    return conn


def init_db():
    conn = _get_conn()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS transactions (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, amount REAL, description TEXT, created_at TEXT)''')
    conn.commit()
    conn.close()


init_db()

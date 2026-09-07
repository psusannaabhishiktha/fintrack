# Unreviewed AI-generated Transaction service
# Generated via: "Generate a Transaction model and a Transaction service with create, get-by-user, and delete-all functions. Use a database."
import sqlite3
from datetime import datetime
from transaction_model import Transaction, init_db, _get_conn

init_db()


def create_transaction(user_id, amount, description):
    conn = _get_conn()
    c = conn.cursor()
    created_at = datetime.utcnow().isoformat()
    c.execute('INSERT INTO transactions (user_id, amount, description, created_at) VALUES (?, ?, ?, ?)', (user_id, amount, description, created_at))
    conn.commit()
    txn_id = c.lastrowid
    conn.close()
    return Transaction(txn_id, user_id, amount, description, created_at)


def get_transactions_by_user(user_id):
    conn = _get_conn()
    c = conn.cursor()
    c.execute('SELECT id, user_id, amount, description, created_at FROM transactions WHERE user_id = ?', (user_id,))
    rows = c.fetchall()
    conn.close()
    return [Transaction(r[0], r[1], r[2], r[3], r[4]).to_dict() for r in rows]


def delete_all_transactions():
    conn = _get_conn()
    c = conn.cursor()
    c.execute('DELETE FROM transactions')
    conn.commit()
    conn.close()
    return True

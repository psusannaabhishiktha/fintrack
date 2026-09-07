from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from typing import List, Dict
from src.transactions.service import ExpenseService, ValidationError

app = FastAPI(title="FinTrack API")
service = ExpenseService()

class ParticipantIn(BaseModel):
    user_id: str
    amount: float | None = None

class CreateExpenseIn(BaseModel):
    description: str
    total_amount: float
    split_type: str
    participants: List[ParticipantIn]

@app.post('/expenses')
def create_expense(payload: CreateExpenseIn, x_user_id: str = Header(...)):
    try:
        exp = service.create_shared_expense(creator=x_user_id, payload=payload.model_dump())
        return {"id": exp.id, "creator": exp.creator, "total_amount": exp.total_amount}
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get('/balances')
def get_balances(x_user_id: str = Header(...)):
    balances = service.get_user_balances(user_id=x_user_id)
    # Format: {counterparty_user_id: net_amount} where positive means user is owed money
    return balances

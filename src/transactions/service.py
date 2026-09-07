from pydantic import BaseModel, Field, field_validator
from typing import List, Dict
from .repository import SessionLocal, ExpenseRepository, init_db
from sqlalchemy.exc import SQLAlchemyError

init_db()

class Participant(BaseModel):
    user_id: str
    amount: float | None = None

class CreateExpenseRequest(BaseModel):
    description: str = Field(..., max_length=512)
    total_amount: float = Field(..., gt=0)
    split_type: str
    participants: List[Participant]

    @field_validator('split_type')
    @classmethod
    def split_type_must_be_valid(cls, v):
        if v not in ('equal', 'custom'):
            raise ValueError('split_type must be either "equal" or "custom"')
        return v

class AuthorizationError(Exception):
    pass

class ValidationError(Exception):
    pass

class ExpenseService:
    def __init__(self):
        self.Session = SessionLocal

    def _validate_and_prepare(self, req: CreateExpenseRequest, creator: str):
        participants = [p.model_dump() for p in req.participants]
        if len(participants) < 2:
            raise ValidationError('At least 2 participants required')
        if req.split_type == 'equal':
            share = round(req.total_amount / len(participants), 2)
            for p in participants:
                p['amount'] = share
        else:
            # custom: ensure all amounts provided and sum to total
            if any(p.get('amount') is None for p in participants):
                raise ValidationError('All participants must include an amount for custom splits')
            total = sum(p['amount'] for p in participants)
            if round(total, 2) != round(req.total_amount, 2):
                raise ValidationError('Custom participant amounts must sum to total_amount')
        return participants

    def create_shared_expense(self, creator: str, payload: dict):
        req = CreateExpenseRequest(**payload)
        participants = self._validate_and_prepare(req, creator)
        session = self.Session()
        repo = ExpenseRepository(session)
        try:
            exp = repo.create_shared_expense(creator=creator, description=req.description, total_amount=req.total_amount, split_type=req.split_type, participants=participants)
            return exp
        except SQLAlchemyError as e:
            session.rollback()
            raise
        finally:
            session.close()

    def get_user_balances(self, user_id: str):
        # compute net balances per counterparty
        session = self.Session()
        repo = ExpenseRepository(session)
        try:
            expenses = repo.list_all_expenses()
            balances = {}  # (user_a, user_b) -> amount user_a owes user_b positive
            # Simplified model: creator paid total; each participant owes their share to creator.
            for e in expenses:
                creator = e.creator
                for p in e.participants:
                    uid = p.get('user_id')
                    amt = float(p.get('amount'))
                    if uid == creator:
                        continue
                    # uid owes creator amt
                    balances.setdefault((uid, creator), 0.0)
                    balances[(uid, creator)] += amt
            # Now compute net per counterparty for requested user
            result = {}
            for (a, b), amt in balances.items():
                if a == user_id or b == user_id:
                    other = b if a == user_id else a
                    # compute net between user_id and other: (other owes user) negative means user owes other
                    key = other
                    if (other, user_id) in balances and (user_id, other) in balances:
                        net = balances.get((user_id, other), 0.0) - balances.get((other, user_id), 0.0)
                    else:
                        net = balances.get((user_id, other), 0.0) - balances.get((other, user_id), 0.0)
                    result[key] = abs(round(net, 2))
            return result
        finally:
            session.close()

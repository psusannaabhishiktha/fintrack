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
        session = self.Session()
        repo = ExpenseRepository(session)
        try:
            expenses = repo.list_all_expenses()
            net_by_counterparty = {}

            for e in expenses:
                creator = e.creator
                for p in e.participants:
                    participant_id = p.get('user_id')
                    amount = float(p.get('amount', 0) or 0)
                    if participant_id == creator:
                        continue

                    if participant_id == user_id:
                        net_by_counterparty[creator] = net_by_counterparty.get(creator, 0.0) - amount
                    elif creator == user_id:
                        net_by_counterparty[participant_id] = net_by_counterparty.get(participant_id, 0.0) + amount

            return {counterparty: round(abs(amount), 2) for counterparty, amount in net_by_counterparty.items() if abs(amount) > 0}
        finally:
            session.close()

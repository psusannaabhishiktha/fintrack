from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from .models import Base, SharedExpense

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
DATABASE_FILE = os.path.join(PROJECT_ROOT, 'fintrack.db')
DATABASE_URL = os.getenv('FINTRACK_DATABASE_URL', f'sqlite:///{DATABASE_FILE}')
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if 'sqlite' in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

class ExpenseRepository:
    def __init__(self, session):
        self.session = session

    def create_shared_expense(self, creator, description, total_amount, split_type, participants):
        expense = SharedExpense(creator=creator, description=description, total_amount=total_amount, split_type=split_type, participants=participants)
        self.session.add(expense)
        self.session.commit()
        self.session.refresh(expense)
        return expense

    def list_expenses_for_user(self, user_id):
        # returns expenses where user is creator or participant
        q = self.session.query(SharedExpense).filter(SharedExpense.participants.contains([{}]))
        # SQLAlchemy JSON contains with SQLite isn't ideal; fallback to load all and filter in Python for simplicity
        expenses = self.session.query(SharedExpense).all()
        return [e for e in expenses if (e.creator == user_id) or any(p.get('user_id') == user_id for p in e.participants)]

    def list_all_expenses(self):
        return self.session.query(SharedExpense).all()

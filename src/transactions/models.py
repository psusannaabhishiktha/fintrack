from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

class Transaction(Base):
    __tablename__ = 'transactions'
    id = Column(Integer, primary_key=True)
    user_id = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    description = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class SharedExpense(Base):
    __tablename__ = 'shared_expenses'
    id = Column(Integer, primary_key=True)
    creator = Column(String, nullable=False)
    description = Column(String)
    total_amount = Column(Float, nullable=False)
    split_type = Column(String, nullable=False)  # 'equal' or 'custom'
    participants = Column(JSON, nullable=False)  # list of {user_id, amount}
    created_at = Column(DateTime, default=datetime.utcnow)

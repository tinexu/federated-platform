from sqlalchemy import Column, String, Integer, Float, DateTime, JSON
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Customer(Base):
    __tablename__ = 'customers'
    
    id = Column(String, primary_key=True)
    email = Column(String, unique=True)
    company_name = Column(String)
    api_key = Column(String, unique=True)
    created_at = Column(DateTime)
    subscription_tier = Column(String)
    
class FLJob(Base):
    __tablename__ = 'fl_jobs'
    
    id = Column(String, primary_key=True)
    customer_id = Column(String)
    name = Column(String)
    status = Column(String)
    config = Column(JSON)
    created_at = Column(DateTime)
    completed_at = Column(DateTime)
    
class JobMetrics(Base):
    __tablename__ = 'job_metrics'
    
    id = Column(String, primary_key=True)
    job_id = Column(String)
    round_number = Column(Integer)
    accuracy = Column(Float)
    loss = Column(Float)
    privacy_spent = Column(Float)
    participating_clients = Column(Integer)
    timestamp = Column(DateTime)
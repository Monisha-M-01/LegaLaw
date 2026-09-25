from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

# Create an SQLite database in the backend directory
SQLALCHEMY_DATABASE_URL = "sqlite:///./sql_app.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True, index=True)
    session_id = Column(String, index=True)
    filename = Column(String)
    upload_timestamp = Column(DateTime, default=datetime.utcnow)
    target_language = Column(String, default="en")
    clauses = Column(JSON, default=list)
    risk_tags = Column(JSON, default=dict)
    summary = Column(JSON, nullable=True)

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(String, index=True)
    role = Column(String) # "user" or "assistant"
    content = Column(Text)
    cited_clause = Column(String, nullable=True)
    is_clarifying = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

# Create tables
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

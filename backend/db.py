# backend/db.py
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# -----------------------------
# 🗄️ Database Setup
# -----------------------------
DATABASE_URL = "sqlite:///./chat_history.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


# -----------------------------
# 💬 Chat History Model
# -----------------------------
class ChatHistory(Base):
    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), index=True)
    user_message = Column(Text)
    bot_reply = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


# -----------------------------
# 🧾 Lead Model
# -----------------------------
class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    email = Column(String(100))
    phone = Column(String(50))
    interest = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)


# -----------------------------
# 🧩 Dependency for FastAPI
# -----------------------------
def get_db():
    """Provides a database session for FastAPI routes"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# backend/models.py
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime


# -----------------------------
# 💬 Chat Models
# -----------------------------
class ChatRequest(BaseModel):
    session_id: str
    message: str


class ChatResponse(BaseModel):
    reply: str
    # The app returns the context used under the name `context_used` in many places.
    # Keep `sources` for backward compatibility and add `context_used` which the
    # routes populate.
    sources: Optional[List[str]] = None
    context_used: Optional[List[str]] = None


# -----------------------------
# 🧾 Lead Models
# -----------------------------
class LeadIn(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    interest: Optional[str] = "AI Courses"


class LeadOut(LeadIn):
    id: int
    # store as datetime so FastAPI/Pydantic will validate correctly
    created_at: Optional[datetime] = None

    class Config:
        # pydantic v2 renamed "orm_mode" to "from_attributes"; set the
        # modern name to avoid deprecation warnings while preserving
        # compatibility with ORMs.
        from_attributes = True


# -----------------------------
# 📚 Knowledge Base Models
# -----------------------------
class KBSearchRequest(BaseModel):
    query: str
    # allow the client to control how many results to return
    top_k: int = 3


class KBSearchResponse(BaseModel):
    # the route returns documents under the name `documents`
    documents: List[str]

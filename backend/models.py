from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime



class ChatRequest(BaseModel):
    session_id: str
    message: str


class ChatResponse(BaseModel):
    reply: str
    sources: Optional[List[str]] = None
    context_used: Optional[List[str]] = None



class LeadIn(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    interest: Optional[str] = "AI Courses"


class LeadOut(LeadIn):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class KBSearchRequest(BaseModel):
    query: str
    top_k: int = 3


class KBSearchResponse(BaseModel):
    
    documents: List[str]

import os
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from sqlalchemy.orm import Session

try:
    from backend.db import get_db, ChatHistory, Lead, Base, engine
    from backend.models import (
        ChatRequest,
        ChatResponse,
        LeadIn,
        LeadOut,
        KBSearchRequest,
        KBSearchResponse,
    )
    from backend.kb_ingest import get_relevant_docs, load_kb
    from backend.llm_client import generate_gemini_response
except Exception:
    
    from db import get_db, ChatHistory, Lead, Base, engine
    from models import (
        ChatRequest,
        ChatResponse,
        LeadIn,
        LeadOut,
        KBSearchRequest,
        KBSearchResponse,
    )
    from kb_ingest import get_relevant_docs, load_kb
    from llm_client import generate_gemini_response


load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("⚠️ Warning: GEMINI_API_KEY not set. Set it in your .env file.")

app = FastAPI(title="Ahsan Courses Chatbot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)


@app.on_event("startup")
def on_startup():
 
    try:
        load_kb()
    except Exception as e:
        print("⚠️ KB load failed at startup:", e)

@app.get("/")
def home():
    return {"message": "Welcome to Ahsan Courses AI Chatbot 🚀"}


@app.get("/kb/status")
def kb_status():
    """Return whether the KB is loaded and how many documents exist."""
    try:
        
        load_kb()
        from backend.kb_ingest import documents as docs
    except Exception:
        
        try:
            from kb_ingest import documents as docs
        except Exception:
            docs = []
    return {"loaded": bool(docs), "documents": len(docs)}


@app.post("/chat", response_model=ChatResponse)
async def chat_with_bot(request: ChatRequest, db: Session = Depends(get_db)):
    """Main chatbot route — AI answers AI-related questions."""
    user_message = request.message.strip()

    context_docs = get_relevant_docs(user_message, top_k=3)
    context_text = "\n\n".join(context_docs)

    try:
        bot_reply = generate_gemini_response(user_message, context_text)
    except Exception as e:
        print("LLM Error:", e)
        raise HTTPException(status_code=500, detail="Gemini API call failed")

    # Save chat to DB
    chat_record = ChatHistory(
        session_id=request.session_id,
        user_message=user_message,
        bot_reply=bot_reply,
    )
    db.add(chat_record)
    db.commit()
    db.refresh(chat_record)

    return ChatResponse(reply=bot_reply, sources=context_docs, context_used=context_docs)


@app.post("/kb/search", response_model=KBSearchResponse)
def search_kb(req: KBSearchRequest):
    """Search KB for AI course info."""
    results = get_relevant_docs(req.query, top_k=req.top_k)
    return KBSearchResponse(documents=results)


# -----------------------------------------
# 🧾 Lead Capture Route
# -----------------------------------------
@app.post("/lead", response_model=LeadOut)
def capture_lead(lead: LeadIn, db: Session = Depends(get_db)):
    """Store user interest / lead information."""
    db_lead = Lead(
        name=lead.name,
        email=lead.email,
        phone=lead.phone,
        interest=lead.interest,
    )
    db.add(db_lead)
    db.commit()
    db.refresh(db_lead)
    return db_lead


# -----------------------------------------
# 📜 Get All Leads (Admin)
# -----------------------------------------
@app.get("/admin/leads", response_model=list[LeadOut])
def get_all_leads(db: Session = Depends(get_db)):
    leads = db.query(Lead).order_by(Lead.created_at.desc()).all()
    return leads


# -----------------------------------------
# 💡 Health Check Route
# -----------------------------------------
@app.get("/health")
def health_check():
    return {"status": "ok", "message": "Backend running fine ✅"}



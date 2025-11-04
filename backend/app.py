# # backend/app.py
# import os, sys
# # ensure backend folder is in path so relative imports work when uvicorn is run from project root
# sys.path.append(os.path.dirname(__file__))

# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# from models import ChatRequest, ChatResponse, LeadIn, KBSearchRequest
# from db import SessionLocal, init_db, Message, Lead
# from llm_client import call_llm_with_context
# from kb_ingest import get_relevant_docs
# from models import ChatRequest, ChatResponse, LeadIn, KBSearchRequest


# app = FastAPI(title="Ahsan Courses Chatbot API")

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# @app.on_event("startup")
# def startup():
#     init_db()

# @app.post("/chat", response_model=ChatResponse)
# def chat(req: ChatRequest):
#     db = SessionLocal()
#     # save user message
#     m = Message(session_id=req.session_id, role="user", content=req.message)
#     db.add(m)
#     db.commit()
#     # get recent history (last 20)
#     msgs = db.query(Message).filter(Message.session_id == req.session_id).order_by(Message.id.desc()).limit(20).all()
#     context = [x.content for x in reversed(msgs)]
#     # retrieve KB context
#     docs = []
#     try:
#         docs = get_relevant_docs(req.message, top_k=3)
#     except Exception as e:
#         docs = []
#     # call LLM
#     resp = call_llm_with_context(req.message, context_docs=docs)
#     assistant_text = resp.get("text", "[LLM error]")
#     # save assistant message
#     db.add(Message(session_id=req.session_id, role="assistant", content=assistant_text))
#     db.commit()
#     db.close()
#     return ChatResponse(reply=assistant_text, sources=[d[:140] for d in docs])

# @app.post("/lead")
# def save_lead(lead: LeadIn):
#     db = SessionLocal()
#     l = Lead(name=lead.name, email=lead.email, phone=lead.phone, interest=lead.interest)
#     db.add(l)
#     db.commit()
#     db.close()
#     return {"status": "ok"}

# @app.get("/history/{session_id}")
# def get_history(session_id: str):
#     db = SessionLocal()
#     msgs = db.query(Message).filter(Message.session_id == session_id).order_by(Message.id).all()
#     db.close()
#     return [{"role": m.role, "content": m.content, "ts": m.created_at.isoformat()} for m in msgs]

# @app.post("/kb/search")
# def kb_search(req: KBSearchRequest):
#     results = get_relevant_docs(req.query, top_k=req.top_k)
#     return {"results": results}

# @app.get("/admin/leads")
# def admin_leads():
#     db = SessionLocal()
#     leads = db.query(Lead).order_by(Lead.created_at.desc()).limit(200).all()
#     db.close()
#     return [{"name": l.name, "email": l.email, "phone": l.phone, "interest": l.interest, "created_at": l.created_at.isoformat()} for l in leads]




 # Correct code with Chatbot Work with 


# backend/app.py
import os
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from sqlalchemy.orm import Session

# Support flexible import paths: allow running `uvicorn backend.app:app` from
# project root, or `uvicorn app:app` when working inside the `backend/` folder.
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
    # fallback to local imports when running inside backend/
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

# -----------------------------------------
# 🌍 Load environment and initialize app
# -----------------------------------------
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("⚠️ Warning: GEMINI_API_KEY not set. Set it in your .env file.")

app = FastAPI(title="Ahsan Courses Chatbot API")

# CORS for Streamlit frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize DB
Base.metadata.create_all(bind=engine)


@app.on_event("startup")
def on_startup():
    # Load the KB on startup (lazy) and catch errors so the server still comes up
    try:
        load_kb()
    except Exception as e:
        print("⚠️ KB load failed at startup:", e)

# -----------------------------------------
# 🏠 Root Route
# -----------------------------------------
@app.get("/")
def home():
    return {"message": "Welcome to Ahsan Courses AI Chatbot API 🚀"}


@app.get("/kb/status")
def kb_status():
    """Return whether the KB is loaded and how many documents exist."""
    try:
        # call load_kb to ensure vectors attempted to be loaded
        load_kb()
        from backend.kb_ingest import documents as docs
    except Exception:
        # try fallback when running inside backend/
        try:
            from kb_ingest import documents as docs
        except Exception:
            docs = []
    return {"loaded": bool(docs), "documents": len(docs)}


# -----------------------------------------
# 💬 Chat Route
# -----------------------------------------
@app.post("/chat", response_model=ChatResponse)
async def chat_with_bot(request: ChatRequest, db: Session = Depends(get_db)):
    """Main chatbot route — AI answers AI-related questions."""
    user_message = request.message.strip()

    # Fetch relevant docs from KB
    context_docs = get_relevant_docs(user_message, top_k=3)
    context_text = "\n\n".join(context_docs)

    # Generate LLM response
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

    # populate both names so clients expecting either field name will work
    return ChatResponse(reply=bot_reply, sources=context_docs, context_used=context_docs)


# -----------------------------------------
# 🧠 KB Search Route
# -----------------------------------------
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



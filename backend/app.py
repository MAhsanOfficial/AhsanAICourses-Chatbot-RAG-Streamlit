import os
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from sqlalchemy.orm import Session

try:
    from backend.db import get_db, ChatHistory, Lead, Enrollment, Base, engine
    from backend.models import (
        ChatRequest,
        ChatResponse,
        LeadIn,
        LeadOut,
        EnrollmentIn,
        EnrollmentOut,
        ChatSaveRequest,
        ChatHistoryOut,
        KBSearchRequest,
        KBSearchResponse,
    )
    from backend.kb_ingest import get_relevant_docs, load_kb
    from backend.llm_client import generate_gemini_response
except Exception:
    
    from db import get_db, ChatHistory, Lead, Enrollment, Base, engine
    from models import (
        ChatRequest,
        ChatResponse,
        LeadIn,
        LeadOut,
        EnrollmentIn,
        EnrollmentOut,
        ChatSaveRequest,
        ChatHistoryOut,
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

    # Check for an explicit request asking for the user's last question.
    # If detected, fetch the most recent user_message for this session and reply directly.
    lower_msg = user_message.lower()
    if (
        "what was my last question" in lower_msg
        or "what was my last query" in lower_msg
        or "last question" == lower_msg
        or lower_msg.endswith("last question?")
    ):
        prev = (
            db.query(ChatHistory)
            .filter(ChatHistory.session_id == request.session_id, ChatHistory.user_message != None)
            .order_by(ChatHistory.created_at.desc())
            .first()
        )
        if prev and prev.user_message:
            bot_reply = f"Your last question was: {prev.user_message}"
        else:
            bot_reply = "I couldn't find any previous question in this session."

        # Save the meta-question and the reply as a chat turn
        chat_record = ChatHistory(
            session_id=request.session_id,
            user_message=user_message,
            bot_reply=bot_reply,
        )
        db.add(chat_record)
        db.commit()
        db.refresh(chat_record)

        return ChatResponse(reply=bot_reply, sources=[], context_used=[])

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


@app.post("/chat/save")
def save_chat_history(payload: ChatSaveRequest, db: Session = Depends(get_db)):
    """Save a list of chat turns (turns are objects with user_message and/or bot_reply).

    Expected payload: { session_id: str, turns: [{user_message, bot_reply, created_at?}, ...] }
    """
    count = 0
    for t in payload.turns:
        ch = ChatHistory(
            session_id=payload.session_id,
            user_message=t.user_message,
            bot_reply=t.bot_reply,
        )
        db.add(ch)
        count += 1
    db.commit()
    return {"status": "ok", "saved": count}


@app.get("/chat/top5", response_model=list[ChatHistoryOut])
def get_top5_chats(db: Session = Depends(get_db)):
    """Return the 5 most recent chat history rows across all sessions."""
    rows = db.query(ChatHistory).order_by(ChatHistory.created_at.desc()).limit(5).all()
    return rows


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


# -----------------------------------------
# 🧾 Enrollment Routes
# -----------------------------------------
@app.post("/enroll", response_model=EnrollmentOut)
def enroll_student(enroll: EnrollmentIn, db: Session = Depends(get_db)):
    """Endpoint to create a course enrollment. Validates required fields and duplicate email/phone."""
    # Basic non-empty validation (Pydantic ensures types but allow non-empty check)
    for field_name, value in ("username", enroll.username), ("email", enroll.email), ("phone", enroll.phone), ("address", enroll.address), ("course", enroll.course):
        if not isinstance(value, str) or not value.strip():
            raise HTTPException(status_code=400, detail="You didn’t provide this information, please fill it.")

    valid_courses = ["AI Automation", "Data Science", "Agentic AI", "Generative AI"]
    if enroll.course not in valid_courses:
        raise HTTPException(status_code=400, detail="This course is not available. Please select one of these 4 AI courses only.")

    # Check duplicates by email or phone
    existing = db.query(Enrollment).filter((Enrollment.email == enroll.email) | (Enrollment.phone == enroll.phone)).first()
    if existing:
        # Inform frontend that user already enrolled
        raise HTTPException(status_code=409, detail="You have already enrolled. Your information is already saved.")

    db_enroll = Enrollment(
        username=enroll.username.strip(),
        email=enroll.email.strip(),
        phone=enroll.phone.strip(),
        address=enroll.address.strip(),
        course=enroll.course,
    )
    db.add(db_enroll)
    db.commit()
    db.refresh(db_enroll)
    return db_enroll


@app.get("/admin/enrollments", response_model=list[EnrollmentOut])
def get_all_enrollments(db: Session = Depends(get_db)):
    rows = db.query(Enrollment).order_by(Enrollment.created_at.desc()).all()
    return rows



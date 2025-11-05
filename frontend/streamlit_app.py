# frontend/streamlit_app.py
import streamlit as st
import requests
import uuid
import os

API_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(
    page_title="Ahsan Courses — AI Chat Assistant",
    layout="wide",
    page_icon="🤖"
)

st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #0f172a, #2563eb);
        color: white;
        padding: 20px;
        border-radius: 12px;
        margin-bottom: 20px;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
    }
    .msg-user {
        text-align: center;
        background: #000000;
        padding: 10px;
        border-radius: 12px;
        margin: 6px 0;
    }
    .msg-bot {
        text-align: left;
        background: #0000FF;
        padding: 10px;
        border-radius: 12px;
        margin: 6px 0;
    }
    .footer {
        text-align:center;
        font-size: 13px;
        color: gray;
        margin-top: 30px;
    }
</style>
<div class="main-header">
    <h1>🤖 Ahsan Courses AI-Chatbot</h1>
    <p>Ask about AI Automation, Data Science, Agentic AI, or Generative AI</p>
</div>
""", unsafe_allow_html=True)

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "asked_enroll" not in st.session_state:
    st.session_state.asked_enroll = False
if "awaiting_enroll_response" not in st.session_state:
    st.session_state.awaiting_enroll_response = False
if "show_enroll_form" not in st.session_state:
    st.session_state.show_enroll_form = False

col1, col2 = st.columns([2.8, 1.2])

with col1:
    st.subheader("💬 Chat with Ahsan AI Courses Bot")
    for role, text in st.session_state.chat_history:
        css_class = "msg-user" if role == "You" else "msg-bot"
        st.markdown(f"<div class='{css_class}'>{text}</div>", unsafe_allow_html=True)

    # If enrollment flow was triggered, show enrollment form here
    if st.session_state.show_enroll_form:
        st.markdown("---")
        st.subheader("📝 Course Enrollment Form")
        with st.form("enroll_form"):
            username = st.text_input("Username")
            email = st.text_input("Email")
            phone = st.text_input("Phone Number")
            address = st.text_area("Address")
            course = st.selectbox("Select Course", [
                "AI Automation", "Data Science", "Agentic AI", "Generative AI"
            ])
            submit_enroll = st.form_submit_button("Enroll")
            if submit_enroll:
                # Validate fields non-empty
                if not username.strip() or not email.strip() or not phone.strip() or not address.strip() or not course.strip():
                    st.session_state.chat_history.append(("AhsanBot", "You didn’t provide this information, please fill it."))
                    st.error("You didn’t provide this information, please fill it.")
                    st.rerun()

                valid_courses = ["AI Automation", "Data Science", "Agentic AI", "Generative AI"]
                if course not in valid_courses:
                    st.session_state.chat_history.append(("AhsanBot", "This course is not available. Please select one of these 4 AI courses only."))
                    st.error("This course is not available. Please select one of these 4 AI courses only.")
                    st.rerun()

                payload = {
                    "username": username,
                    "email": email,
                    "phone": phone,
                    "address": address,
                    "course": course,
                }
                try:
                    r = requests.post(f"{API_URL}/enroll", json=payload, timeout=8)
                    if r.ok:
                        st.session_state.chat_history.append(("You", f"[Enrollment form submitted]"))
                        st.session_state.chat_history.append(("AhsanBot", "You are successfully enrolled!"))
                        st.success("You are successfully enrolled!")
                        # hide form after success
                        st.session_state.show_enroll_form = False
                        st.rerun()
                    else:
                        if r.status_code == 409:
                            st.session_state.chat_history.append(("AhsanBot", "You have already enrolled. Your information is already saved."))
                            st.warning("You have already enrolled. Your information is already saved.")
                        else:
                            try:
                                msg = r.json().get("detail") or r.text
                            except Exception:
                                msg = r.text
                            st.error(f"Enrollment failed: {msg}")
                except Exception as e:
                    st.error(f"Network error submitting enrollment: {e}")
                    st.session_state.chat_history.append(("System", f"Error: {e}"))
                    st.rerun()

    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_area("Type your question", height=100, placeholder="e.g. Tell me about Generative AI course...")
        send = st.form_submit_button("Send")
        if send and user_input.strip():
            # If we were waiting for a yes/no reply to the enrollment question, intercept it
            user_text = user_input.strip()
            lower = user_text.lower()
            yes_triggers = ["yes", "haan", "haan!", "haan.", "y", "yeah", "yep", "ya", "yea"]
            if st.session_state.awaiting_enroll_response:
                # check for affirmative
                if any(token in lower for token in yes_triggers):
                    st.session_state.chat_history.append(("You", user_text))
                    st.session_state.chat_history.append(("AhsanBot", "Great — please fill the form below to enroll."))
                    st.session_state.show_enroll_form = True
                    st.session_state.awaiting_enroll_response = False
                    st.rerun()
                else:
                    st.session_state.chat_history.append(("You", user_text))
                    st.session_state.chat_history.append(("AhsanBot", "No problem — let me know if you change your mind."))
                    st.session_state.awaiting_enroll_response = False
                    st.rerun()

            # Normal chat flow
            payload = {"session_id": st.session_state.session_id, "message": user_text}
            try:
                r = requests.post(f"{API_URL}/chat", json=payload)
                if r.ok:
                    data = r.json()
                    # detect if this was the very first user message in the session
                    user_count = sum(1 for role, _ in st.session_state.chat_history if role == "You")
                    is_first_user = user_count == 0

                    st.session_state.chat_history.append(("You", user_text))
                    st.session_state.chat_history.append(("AhsanBot", data["reply"]))

                    # after first reply, ask about enrollment automatically
                    if is_first_user and not st.session_state.asked_enroll:
                        st.session_state.chat_history.append(("AhsanBot", "Would you like to enroll in a course?"))
                        st.session_state.awaiting_enroll_response = True
                        st.session_state.asked_enroll = True
                else:
                    st.session_state.chat_history.append(("System", "⚠️ Backend error"))
            except Exception as e:
                st.session_state.chat_history.append(("System", f"Error: {e}"))
            st.rerun()

with col2:
    st.subheader("📩 Interested in a Course?")
    with st.form("lead_form"):
        name = st.text_input("Your Name")
        email = st.text_input("Email")
        phone = st.text_input("Phone (optional)")
        interest = st.selectbox("Select a course", [
            "AI Automation", "Data Science", "Agentic AI", "Generative AI"
        ])
        submit_lead = st.form_submit_button("Submit Lead")
        if submit_lead:
            lead_payload = {"name": name, "email": email, "phone": phone, "interest": interest}
            try:
                r = requests.post(f"{API_URL}/lead", json=lead_payload, timeout=8)
                if r.ok:
                    st.success("✅ Thanks! Our team will contact you soon.")
                else:
                    # show backend response text for easier debugging
                    try:
                        msg = r.json()
                    except Exception:
                        msg = r.text
                    st.error(f"❌ Failed to submit lead. Server response: {msg}")
            except Exception as e:
                st.error(f"❌ Failed to submit lead (network error): {e}")

    st.markdown("---")
    st.subheader("📘 Quick Course Outlines")
    course_choice = st.radio("Pick course", [
        "AI Automation", "Data Science", "Agentic AI", "Generative AI"
    ])
    if st.button("Show Outline"):
        q = f"Give a complete outline of the {course_choice} course."
        payload = {"session_id": st.session_state.session_id, "message": q}
        try:
            r = requests.post(f"{API_URL}/chat", json=payload, timeout=15)
            if r.ok:
                data = r.json()
            
                reply = data.get("reply") or data.get("text") or str(data)
                st.info(reply)
            else:
                try:
                    msg = r.json()
                except Exception:
                    msg = r.text
                st.error(f"Backend error: {msg}")
        except Exception as e:
            st.error(f"Network error calling backend: {e}")

    st.markdown("---")
    st.subheader("🧾 Admin Panel (for you)")
    if st.button("Show Latest Leads"):
        try:
            r = requests.get(f"{API_URL}/admin/leads")
            if r.ok:
                leads = r.json()
                for lead in leads[:10]:
                    st.write(
                        f"**{lead['name']}** — {lead['email']} ({lead['interest']})  "
                        f"<br><small>{lead['created_at']}</small>", unsafe_allow_html=True
                    )
            else:
                st.warning("No leads found.")
        except Exception as e:
            st.error(f"Error fetching leads: {e}")

st.markdown("""
<div class="footer">
    Made with ❤️ by Ahsan — Powered by Gemini & Streamlit and always Ahsan
</div>
""", unsafe_allow_html=True)

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
    <h1>🤖 Ahsan Courses Chatbot</h1>
    <p>Ask about AI Automation, Data Science, Agentic AI, or Generative AI</p>
</div>
""", unsafe_allow_html=True)

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

col1, col2 = st.columns([2.8, 1.2])

with col1:
    st.subheader("💬 Chat with AhsanBot")
    for role, text in st.session_state.chat_history:
        css_class = "msg-user" if role == "You" else "msg-bot"
        st.markdown(f"<div class='{css_class}'>{text}</div>", unsafe_allow_html=True)

    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_area("Type your question", height=100, placeholder="e.g. Tell me about Generative AI course...")
        send = st.form_submit_button("Send")
        if send and user_input.strip():
            payload = {"session_id": st.session_state.session_id, "message": user_input}
            try:
                r = requests.post(f"{API_URL}/chat", json=payload)
                if r.ok:
                    data = r.json()
                    st.session_state.chat_history.append(("You", user_input))
                    st.session_state.chat_history.append(("AhsanBot", data["reply"]))
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
                # defensive: accept either 'reply' or 'reply' nested patterns
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
    Made with ❤️ by Ahsan — Powered by Gemini & Streamlit
</div>
""", unsafe_allow_html=True)

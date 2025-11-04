# Ahsan Courses Chatbot

## Overview
A FastAPI + Streamlit chatbot that answers ONLY about AI courses:
- AI Automation
- Data Science
- Agentic AI
- Generative AI

Chat history stored in SQLite (messages). Knowledge base stored in `data/knowledge_base.db` using Gemini embeddings.

## Setup (local)
1. Clone/copy the project.
2. Create a Python virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate   # mac/linux
   venv\Scripts\activate      # windows

import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


def _extract_text_from_genai_resp(resp) -> str:
    """Try several common response shapes from google generative ai client."""
    if resp is None:
        return ""
    
    try:
        if isinstance(resp, dict):
            if "candidates" in resp and resp["candidates"]:
                cand = resp["candidates"][0]
                
                text = cand.get("content") or cand.get("output") or cand.get("text")
                if isinstance(text, str):
                    return text
                if isinstance(text, list):
                    
                    return " ".join([t.get("text", "") if isinstance(t, dict) else str(t) for t in text])
       
        if hasattr(resp, "text"):
            return getattr(resp, "text")
        
        return str(resp)
    except Exception:
        return str(resp)


def generate_gemini_response(user_input, context):
    
    if os.getenv("GEMINI_API_KEY") in (None, "", "None"):
        return "[GEMINI_API_KEY not configured — set it in .env to enable live responses]"
    
    try:
        
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        
        prompt = f"""You are Ahsan Courses AI Chatbot assistant. You help users learn about our AI courses.
        You ONLY answer questions about these course categories:
        - AI Automation
        - Data Science
        - Agentic AI
        - Generative AI

        Be professional and concise. If someone asks about topics outside these courses,
        politely decline and offer to take their contact information or suggest exploring our course catalog.

        When describing courses, include:
        - Course duration
        - Prerequisites
        - Key topics covered
        - Learning outcomes
        - Next steps for enrollment

        Use this course context to answer accurately:
        {context}

        User Question: {user_input}
        """

        
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.7,
                top_p=0.8,
                top_k=40,
                max_output_tokens=2048,
            ),
            safety_settings=[
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
            ]
        )
        
        if response.text:
            return response.text
        return _extract_text_from_genai_resp(response)
        
    except Exception as e:
        print(f"LLM Error: {str(e)}")
        return f"[LLM error: {str(e)}]"

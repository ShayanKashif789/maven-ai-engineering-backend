from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from assignments.config import settings
def get_llm():
    return ChatGroq(
        model=settings.LLM_MODEL,
        api_key=settings.GOOGLE_API_KEY,
        temperature=settings.LLM_TEMPERATURE,
        timeout=30
    )
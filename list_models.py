import os
from google import genai
from assignments.config import settings

# Attempt to configure and list models
try:
    client = genai.Client(api_key=settings.GOOGLE_API_KEY)
    print("Listing available models...")
    for model in client.models.list(config={"query_base": True}):
        print(model.name)
except Exception as e:
    print(f"Error: {e}")

import os
import sys

sys.path.append(os.path.dirname(__file__))

from app.config import get_genai_client, LLM_MODEL, GEMINI_API_VERSION

client = get_genai_client()
print(f"Configured LLM_MODEL: {LLM_MODEL}")
print(f"Configured GEMINI_API_VERSION: {GEMINI_API_VERSION}")
print("Available models:")
for model in client.models.list():
    if "flash" in model.name or "gemini" in model.name:
        print(f" - {model.name}")

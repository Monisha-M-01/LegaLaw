import os
import sys
from app.config import get_genai_client
from google.genai import types

client = get_genai_client(api_key=os.environ.get('GEMINI_TRANSLATE_API_KEY'))
candidates = [
    'gemini-3.5-flash',
    'gemini-3.5-flash-lite',
    'gemini-3.7-flash',
    'gemini-3.1-flash-lite-preview',
    'gemini-flash-latest',
    'gemini-flash-lite-latest',
    'gemini-3-flash-preview',
    'gemini-3.6-flash',
    'gemini-3.8-flash',
    'gemini-3.1-flash-lite',
    'gemini-2.5-flash'
]

for m in candidates:
    try:
        res = client.models.generate_content(
            model=m,
            contents='Say hello in Kannada as JSON: {"text": "..."}',
            config=types.GenerateContentConfig(response_mime_type='application/json')
        )
        print(f"{m}: SUCCESS -> length={len(res.text) if res.text else 0}")
    except Exception as e:
        err = str(e)
        code = '503' if '503' in err else ('404' if '404' in err else err[:50])
        print(f"{m}: FAILED ({code})")

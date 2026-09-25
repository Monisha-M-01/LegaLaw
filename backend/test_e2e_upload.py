"""
End-to-end test: mimics what the upload endpoint does.
1. Verifies env key presence
2. Calls generate_content_resilient with a real JSON clause extraction prompt
3. Parses the JSON result
"""
import os
import sys
import json
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config import LLM_MODEL, GEMINI_API_KEY, get_genai_client, generate_content_resilient
from app.services.prompts import INDIAN_LAW_SYSTEM_PROMPT
from google.genai import types

print("=== KEY CHECK ===")
print(f"GEMINI_API_KEY present: {bool(GEMINI_API_KEY)}")
print(f"LLM_MODEL: {LLM_MODEL}")
print()

SAMPLE_TEXT = """
1. RENT AND PAYMENT
The tenant agrees to pay a monthly rent of Rs. 25,000 (Twenty-Five Thousand Rupees) 
on or before the 5th of each month. Late payment will attract a penalty of Rs. 500 per day.

2. SECURITY DEPOSIT
A security deposit of Rs. 1,00,000 is to be paid at the time of signing. 
This deposit is non-refundable if the tenant vacates before the end of the agreement term.

3. TERMINATION
Either party may terminate this agreement with 30 days written notice. 
However, the landlord reserves the right to terminate without notice if the tenant 
fails to pay rent for more than 15 days.
"""

prompt = f"""
You are a legal document analyzer. Break down the following legal document into its distinct clauses.
For each clause, provide:
1. "original": The exact original text of the clause.
2. "simplified": A plain English translation of the clause.
3. "risk": Tag the risk level as "safe", "caution", or "flag".
4. "explanation": A brief explanation of the risk (or why it is safe) in English.

DOCUMENT TEXT:
{SAMPLE_TEXT}

Respond strictly with a JSON array of these clause objects.
"""

print("=== CALLING generate_content_resilient ===")
client = get_genai_client(api_key=GEMINI_API_KEY)
try:
    response = generate_content_resilient(
        client=client,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=INDIAN_LAW_SYSTEM_PROMPT,
            temperature=0.2,
            max_output_tokens=8192,
            response_mime_type="application/json",
        ),
        preferred_model=LLM_MODEL
    )
    raw_text = response.text.strip()
    print(f"Raw response (first 300 chars): {raw_text[:300]}")
    
    clauses = json.loads(raw_text)
    print(f"\nSUCCESS! Extracted {len(clauses)} clauses.")
    for i, c in enumerate(clauses):
        print(f"  Clause {i+1}: risk={c.get('risk')}, simplified={c.get('simplified', '')[:60]}...")
        
except Exception as e:
    print(f"FAILED! {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n=== TEST PASSED ===")

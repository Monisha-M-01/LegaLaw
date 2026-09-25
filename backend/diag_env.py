import os
from dotenv import load_dotenv

load_dotenv()

print("=== ENV VARIABLE DIAGNOSIS ===")
key1 = os.getenv("GEMINI_API_KEY")
key2 = os.getenv("GEMINI_CHAT_API_KEY")
key3 = os.getenv("GEMINI_VERDICT_API_KEY")
key4 = os.getenv("GEMINI_TRANSLATE_API_KEY")
model = os.getenv("LLM_MODEL")
version = os.getenv("GEMINI_API_VERSION")

print("GEMINI_API_KEY present:", bool(key1))
print("GEMINI_CHAT_API_KEY present:", bool(key2))
print("GEMINI_VERDICT_API_KEY present:", bool(key3))
print("GEMINI_TRANSLATE_API_KEY present:", bool(key4))
print("LLM_MODEL:", model)
print("GEMINI_API_VERSION:", version)

if key1:
    print("GEMINI_API_KEY first 10 chars:", key1[:10] + "...")
    print("GEMINI_API_KEY last 5 chars: ..." + key1[-5:])
    print("GEMINI_API_KEY length:", len(key1))
    # Check for hidden characters
    print("GEMINI_API_KEY has quotes?", key1.startswith('"') or key1.startswith("'"))
    print("GEMINI_API_KEY repr of first char:", repr(key1[0]))

print("")
print("=== TESTING ISOLATED LLM CALL ===")
try:
    from google import genai
    from google.genai import types

    http_opts = types.HttpOptions(api_version=version or "v1beta")
    client = genai.Client(api_key=key1, http_options=http_opts)

    print(f"Calling model: {model}")
    response = client.models.generate_content(
        model=model,
        contents="Say 'hello' in exactly one word.",
        config=types.GenerateContentConfig(
            max_output_tokens=10,
            temperature=0.0
        )
    )
    print("SUCCESS! Response:", response.text)
except Exception as e:
    print("FAILED! Error type:", type(e).__name__)
    print("Full error:", str(e))
    import traceback
    traceback.print_exc()

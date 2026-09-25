import os
from dotenv import load_dotenv
load_dotenv()

from google import genai
from google.genai import types

key = os.getenv("GEMINI_API_KEY")
model = os.getenv("LLM_MODEL", "gemini-3-flash-preview")
version = os.getenv("GEMINI_API_VERSION", "v1beta")

http_opts = types.HttpOptions(api_version=version)
client = genai.Client(api_key=key, http_options=http_opts)

print("=== FULL RESPONSE INSPECTION ===")
print(f"Model: {model}")
response = client.models.generate_content(
    model=model,
    contents="Say hello",
    config=types.GenerateContentConfig(max_output_tokens=20, temperature=0.0)
)

print("response object:", response)
print("response.text:", repr(response.text))
print("response.candidates:", response.candidates)
if response.candidates:
    for i, cand in enumerate(response.candidates):
        print(f"  candidate[{i}]:", cand)
        print(f"  candidate[{i}].content:", cand.content)
        print(f"  candidate[{i}].finish_reason:", cand.finish_reason)
        if cand.content and cand.content.parts:
            for j, part in enumerate(cand.content.parts):
                print(f"    part[{j}]:", part)
                print(f"    part[{j}].text:", repr(part.text))

print("")
print("=== TESTING ALL FALLBACK MODELS ===")
fallback_models = ["gemini-3-flash-preview", "gemini-3.6-flash", "gemini-3.8-flash", "gemini-3.1-flash-lite", "gemini-2.0-flash", "gemini-1.5-flash"]
for m in fallback_models:
    try:
        r = client.models.generate_content(
            model=m,
            contents="Say hello",
            config=types.GenerateContentConfig(max_output_tokens=10, temperature=0.0)
        )
        print(f"  {m}: text={repr(r.text)}, candidates={len(r.candidates) if r.candidates else 0}")
    except Exception as e:
        err = str(e)[:100]
        print(f"  {m}: ERROR - {type(e).__name__}: {err}")

print("")
print("=== LISTING AVAILABLE MODELS ===")
try:
    models = client.models.list()
    flash_models = [m for m in models if "flash" in m.name.lower() or "pro" in m.name.lower()]
    for m in flash_models[:15]:
        print(f"  {m.name} - {getattr(m, 'display_name', 'N/A')}")
except Exception as e:
    print(f"  Could not list models: {e}")

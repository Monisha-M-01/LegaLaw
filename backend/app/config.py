import os
import time
import logging
from typing import Optional, List
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

logger = logging.getLogger("ai_legal_assistant")

# Centralized LLM Model configuration
LLM_MODEL: str = os.getenv("LLM_MODEL", "gemini-3-flash-preview")
GEMINI_API_VERSION: str = os.getenv("GEMINI_API_VERSION", "v1beta")

# API Keys
GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")
GEMINI_CHAT_API_KEY: Optional[str] = os.getenv("GEMINI_CHAT_API_KEY") or GEMINI_API_KEY
GEMINI_VERDICT_API_KEY: Optional[str] = os.getenv("GEMINI_VERDICT_API_KEY") or GEMINI_API_KEY
GEMINI_TRANSLATE_API_KEY: Optional[str] = os.getenv("GEMINI_TRANSLATE_API_KEY") or GEMINI_API_KEY

def get_genai_client(api_key: Optional[str] = None) -> genai.Client:
    """
    Creates and returns a genai.Client configured with the target API version and API key.
    """
    key = api_key or GEMINI_API_KEY
    http_opts = types.HttpOptions(api_version=GEMINI_API_VERSION)
    if key:
        return genai.Client(api_key=key, http_options=http_opts)
    return genai.Client(http_options=http_opts)

def verify_llm_connection() -> None:
    """
    Performs a minimal test call to verify the model and API version configuration.
    Fails loudly by raising RuntimeError if the model or API version is invalid.
    """
    logger.info(f"Performing LLM startup health check using model '{LLM_MODEL}' (API version: '{GEMINI_API_VERSION}')...")
    client = get_genai_client()
    try:
        response = client.models.generate_content(
            model=LLM_MODEL,
            contents="Reply with the single word: ready",
            config=types.GenerateContentConfig(
                max_output_tokens=64,
                temperature=0.0
            )
        )
        # Check finish_reason: MAX_TOKENS means the model was truncated — treat as failure
        if response and response.candidates:
            finish_reason = response.candidates[0].finish_reason
            finish_name = finish_reason.name if hasattr(finish_reason, 'name') else str(finish_reason)
            if finish_name == 'MAX_TOKENS':
                raise RuntimeError(
                    f"LLM health check returned MAX_TOKENS — model needs higher max_output_tokens."
                )
        if not response or not response.text:
            raise RuntimeError("LLM returned empty response during health check.")
        logger.info(f"LLM startup health check passed for model '{LLM_MODEL}'.")
    except Exception as exc:
        # Re-raise so the lifespan handler can decide whether to crash or warn.
        # Include a clear "CRITICAL" prefix so callers and tests can detect startup failures.
        raise RuntimeError(
            f"CRITICAL: LLM startup health check failed for model '{LLM_MODEL}' on API version '{GEMINI_API_VERSION}'. "
            f"Error: {exc}"
        ) from exc

def generate_content_resilient(
    client: genai.Client,
    contents: str,
    config: types.GenerateContentConfig,
    preferred_model: Optional[str] = None
) -> types.GenerateContentResponse:
    """
    Calls generate_content with automatic fallback to secondary models if transient
    high-demand (503) or unavailability errors occur.
    """
    primary = preferred_model or LLM_MODEL
    # Try preferred model first, then confirmed-available fallbacks.
    # NOTE: gemini-2.0-flash and gemini-1.5-flash are 404 on v1beta — do NOT add them.
    candidate_models: List[str] = [primary]
    # Fallback chain — verified against this API key's v1beta availability.
    # gemini-2.5-flash and gemini-2.5-flash-lite are 404 for this key (deprecated for new users).
    # gemini-3.6-flash and gemini-3.5-flash-lite are the API-recommended replacements.
    fallbacks = [
        "gemini-3-flash-preview",      # primary preview (may be 503 under high demand)
        "gemini-3.6-flash",            # API-recommended stable; see error msg from gemini-2.5-flash
        "gemini-3.5-flash-lite",       # API-recommended lightweight; see error msg from gemini-2.5-flash-lite
        "gemini-3.1-flash-lite-preview",  # additional stable option visible in models list
    ]
    for m in fallbacks:
        if m not in candidate_models:
            candidate_models.append(m)

    last_error: Optional[Exception] = None
    for model_name in candidate_models:
        for attempt in range(3):
            try:
                logger.info(f"Executing LLM call with model '{model_name}' (attempt {attempt + 1})...")
                response = client.models.generate_content(
                    model=model_name,
                    contents=contents,
                    config=config
                )
                # Explicitly guard against MAX_TOKENS truncation.
                # A thinking model that hits the token cap returns response.text = None
                # or a partial JSON that will fail to parse — treat it as a retriable error.
                if response and response.candidates:
                    finish_reason = response.candidates[0].finish_reason
                    finish_name = finish_reason.name if hasattr(finish_reason, 'name') else str(finish_reason)
                    if finish_name == 'MAX_TOKENS':
                        logger.warning(
                            f"Model '{model_name}' hit MAX_TOKENS on attempt {attempt + 1} — "
                            f"response truncated. Check max_output_tokens in GenerateContentConfig."
                        )
                        last_error = RuntimeError(
                            f"Model '{model_name}' response was truncated (MAX_TOKENS). "
                            f"Increase max_output_tokens in the caller's GenerateContentConfig."
                        )
                        break  # No point retrying same model if it's a token budget issue
                if response and response.text and response.text.strip():
                    return response
                logger.warning(f"Model '{model_name}' returned empty response text (attempt {attempt + 1}).")
                last_error = RuntimeError(f"Model '{model_name}' returned empty/None response text.")
            except Exception as exc:
                last_error = exc
                err_str = str(exc)
                logger.warning(f"Model '{model_name}' error (attempt {attempt + 1}): {err_str[:200]}")
                # 404 = model not found for this API version — skip to next model immediately
                if "404" in err_str or "NOT_FOUND" in err_str:
                    break
                # 429 = quota exhausted — skip to next model, don't pointlessly retry the same one
                if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                    logger.warning(f"Model '{model_name}' quota exhausted — skipping to next fallback.")
                    break
                # 503 = API capacity pressure — wait longer before retry so demand can clear
                logger.warning(f"Model '{model_name}' under high demand (503) — waiting 15s before retry.")
                time.sleep(15)

    raise last_error or RuntimeError("All candidate LLM models failed.")

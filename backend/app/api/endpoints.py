from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
import shutil
import json
import uuid
import os
import re
import time
from tempfile import NamedTemporaryFile
from typing import Optional, List, Dict, Any

from app.services.document_parser import extract_text_from_document
from app.services.chunker import chunk_text
from app.services.vector_store import store_chunks, retrieve_statute_chunks, get_statute_coverage, retrieve_relevant_chunks
from app.database import get_db, Document, Conversation
from app.services.prompts import INDIAN_LAW_SYSTEM_PROMPT
from app.config import LLM_MODEL, get_genai_client, generate_content_resilient, logger
from google.genai import types

def _extract_json(text: str):
    """
    Robustly extract the first JSON array or object from LLM output.
    Handles cases where the model wraps JSON in markdown fences, adds trailing
    explanations, or returns multiple concatenated JSON values.
    """
    # Strip markdown code fences if present
    cleaned = text.strip()
    if cleaned.startswith("```"):
        # Remove opening fence (with optional language tag)
        cleaned = re.sub(r'^```[a-zA-Z]*\n?', '', cleaned, count=1)
        # Remove closing fence
        cleaned = re.sub(r'\n?```\s*$', '', cleaned, count=1)
        cleaned = cleaned.strip()

    # Try parsing as-is first (fast path)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Find the first '[' or '{' and use a decoder to consume exactly one value
    for i, ch in enumerate(cleaned):
        if ch in ('[', '{'):
            decoder = json.JSONDecoder()
            try:
                obj, _ = decoder.raw_decode(cleaned, i)
                return obj
            except json.JSONDecodeError:
                continue

    # Last resort — let json.loads raise a clear error
    return json.loads(cleaned)


LANGUAGE_MAP = {
    "en": "English",
    "hi": "Hindi",
    "kn": "Kannada",
    "ta": "Tamil",
    "te": "Telugu",
    "ml": "Malayalam",
    "kok": "Konkani"
}

router = APIRouter()

class ConversationTurn(BaseModel):
    question: str
    answer: str

class ChatRequest(BaseModel):
    question: str
    conversation_history: List[ConversationTurn] = []
    target_language: str = "en"

class ChatResponse(BaseModel):
    type: str = "answer" # "answer" or "clarification"
    answer: Optional[str] = None
    question: Optional[str] = None
    cited_clauses: List[str] = []
    cited_statutes: List[Dict[str, str]] = []
    confidence: str = "high"

@router.post("/upload")
def upload_document(
    file: UploadFile = File(...),
    session_id: Optional[str] = Form(None),
    target_language: str = Form("en"),
    db: Session = Depends(get_db)
):
    """
    Endpoint to upload a PDF or DOCX file, extract its text, and chunk it.
    If session_id is provided, stores the document in history.
    """
    allowed_extensions = [".pdf", ".docx"]
    file_ext = os.path.splitext(file.filename)[1].lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files are supported.")
    
    if target_language not in ["en", "hi", "kn", "ta", "te", "ml", "kok"]:
        raise HTTPException(status_code=400, detail="Unsupported target language. Choose from 'en', 'hi', 'kn', 'ta', 'te', 'ml', 'kok'.")
    
    tmp_path = None
    # Save the file temporarily
    try:
        suffix = file_ext
        with NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name
        
        # Extract text
        raw_text = extract_text_from_document(tmp_path, file_ext)
        if not raw_text or not raw_text.strip():
            raise HTTPException(
                status_code=400,
                detail={"error_code": "empty_document", "message": "The uploaded document contains no readable text. Please upload a valid document."}
            )
        
        # Chunk text
        chunks = chunk_text(raw_text)
        
        # Clean up temp file
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
            tmp_path = None
        
        # Generate a unique document ID
        document_id = str(uuid.uuid4())
        
        # Store chunks in ChromaDB
        store_chunks(document_id, chunks)
        
        target_lang_name = LANGUAGE_MAP.get(target_language, "English")
        # LLM generation logic
        prompt = f"""
You are a legal document analyzer. Break down the following legal document into its distinct clauses.
For each clause, provide:
1. "original": The exact original text of the clause.
2. "simplified": A plain {target_lang_name} translation of the clause.
3. "risk": Tag the risk level as "safe", "caution", or "flag".
4. "explanation": A brief explanation of the risk (or why it is safe) in {target_lang_name}.

DOCUMENT TEXT:
{raw_text}

Respond strictly with a JSON array of these clause objects.
"""
        client = get_genai_client(api_key=os.environ.get("GEMINI_API_KEY"))
        extracted_clauses = None
        try:
            response = generate_content_resilient(
                client=client,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=INDIAN_LAW_SYSTEM_PROMPT,
                    temperature=0.2,
                    max_output_tokens=8192,  # Required: thinking models default is tiny; large clause arrays need budget
                    response_mime_type="application/json",
                ),
                preferred_model=LLM_MODEL
            )
            raw_response_text = response.text.strip()
            extracted_clauses = _extract_json(raw_response_text)
            
            # Ensure each clause has an ID
            for i, c in enumerate(extracted_clauses):
                c['id'] = str(i + 1)
        except Exception as e:
            logger.critical(f"Clause extraction failed across candidate models: {e}", exc_info=True)
            raise HTTPException(
                status_code=503,
                detail={"error_code": "llm_unavailable", "message": "Something went wrong on our end, please try again."}
            )

        # Calculate risk tags
        risk_tags = {"safe": 0, "caution": 0, "flag": 0}
        for c in extracted_clauses:
            risk = c.get('risk', 'safe').lower()
            if risk in risk_tags:
                risk_tags[risk] += 1

        # Save to DB if session_id is provided
        if session_id:
            new_doc = Document(
                id=document_id,
                session_id=session_id,
                filename=file.filename,
                target_language=target_language,
                clauses=extracted_clauses,
                risk_tags=risk_tags
            )
            db.add(new_doc)
            db.commit()

        return {
            "document_id": document_id,
            "filename": file.filename,
            "total_chunks": len(chunks),
            "chunks": chunks,
            "clauses": extracted_clauses
        }
    except HTTPException:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise
    except ValueError as ve:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)
        logger.warning(f"Invalid document format or empty content: {ve}")
        raise HTTPException(
            status_code=400,
            detail={"error_code": "invalid_document", "message": str(ve)}
        )
    except Exception as e:
        logger.error(f"Unexpected error in upload_document: {e}", exc_info=True)
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise HTTPException(
            status_code=500,
            detail={"error_code": "internal_error", "message": "Something went wrong on our end, please try again."}
        )

@router.get("/sessions/{session_id}/documents")
def get_session_documents(session_id: str, db: Session = Depends(get_db)):
    """
    Returns a list of previously processed documents for a given session.
    """
    docs = db.query(Document).filter(Document.session_id == session_id).order_by(Document.upload_timestamp.desc()).all()
    return [
        {
            "document_id": doc.id,
            "filename": doc.filename,
            "upload_timestamp": doc.upload_timestamp
        }
        for doc in docs
    ]

@router.get("/statute-coverage")
def statute_coverage():
    """
    Returns which acts and how many sections are currently indexed in the reference corpus.
    """
    return get_statute_coverage()

@router.get("/documents/{document_id}")
def get_document(document_id: str, db: Session = Depends(get_db)):
    """
    Returns full saved state (clauses, risk tags, conversation thread) of a document.
    """
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    conversations = db.query(Conversation).filter(Conversation.document_id == document_id).order_by(Conversation.timestamp.asc()).all()
    
    return {
        "document_id": doc.id,
        "filename": doc.filename,
        "upload_timestamp": doc.upload_timestamp,
        "clauses": doc.clauses,
        "risk_tags": doc.risk_tags,
        "conversation": [
            {
                "role": msg.role,
                "content": msg.content,
                "cited_clause": msg.cited_clause,
                "is_clarifying": msg.is_clarifying,
                "timestamp": msg.timestamp
            } for msg in conversations
        ]
    }

@router.post("/documents/{document_id}/ask", response_model=ChatResponse)
def ask_document(document_id: str, request: ChatRequest, db: Session = Depends(get_db)):
    """
    Q&A endpoint leveraging Dual-RAG and Gemini.
    """
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    # 1. Dual RAG Retrieval
    user_chunks = retrieve_relevant_chunks(request.question, n_results=3, document_id=document_id)
    doc_context = "\n".join([f"Clause ID {c['metadata']['chunk_id']}: {c['text']}" for c in user_chunks])
    
    statute_chunks = retrieve_statute_chunks(request.question, n_results=3)
    statute_context = "\n".join([f"Act: {c['metadata']['act_name']} Section {c['metadata']['section_number']}: {c['text']}" for c in statute_chunks])
    
    # 2. Prepare Context and Prompt
    history_text = ""
    if request.conversation_history:
        history_text = "--- PREVIOUS CONVERSATION ---\n"
        for turn in request.conversation_history[-5:]:
            history_text += f"User: {turn.question}\nAssistant: {turn.answer}\n\n"
            
    last_bot_msg = db.query(Conversation).filter(Conversation.document_id == document_id, Conversation.role == "assistant").order_by(Conversation.timestamp.desc()).first()
    was_last_clarifying = last_bot_msg.is_clarifying if last_bot_msg else False
            
    target_lang_name = LANGUAGE_MAP.get(request.target_language, "English")
    prompt = f"""
{history_text}
--- DOCUMENT CLAUSES (from the user's uploaded file) ---
{doc_context if doc_context else "No relevant clauses found in document."}

--- RELEVANT INDIAN LAW (statute reference) ---
{statute_context if statute_context else "No relevant Indian law found in reference corpus."}

USER QUESTION: {request.question}

WAS_LAST_CLARIFYING: {was_last_clarifying}

INSTRUCTIONS:
You must respond in valid JSON format matching exactly this structure:
{{
    "can_answer": boolean,
    "missing_info": "string (what specifics are missing) or null",
    "clarifying_question": "string (the targeted question to ask the user) or null",
    "final_answer": "string (the actual answer) or null",
    "confidence": "high or low"
}}

RULES:
1. Assess if the user's question can be answered confidently from the Document Clauses and Relevant Indian Law alone.
2. If context is missing/ambiguous (e.g. they ask "is this legal?" without specifying what "this" is):
   - Set `can_answer` to false.
   - Describe what is missing in `missing_info` and provide a targeted `clarifying_question`.
   - EXCEPTION: If WAS_LAST_CLARIFYING is True, you MUST NOT ask another clarification. You must set `can_answer` to true, provide a best-effort `final_answer`, and set `confidence` to "low".
3. If you can answer the question (or are forced to by the exception above):
   - Set `can_answer` to true.
   - Write the `final_answer` strictly in: {target_lang_name}.
   - If citing a law, use the exact Act and Section from the 'RELEVANT INDIAN LAW' section. Do not invent citations.
   - Set `confidence` to "high" if you are certain, or "low" if making a best-effort attempt due to ambiguity.
"""

    # 3. Call Gemini
    client = get_genai_client(api_key=os.environ.get("GEMINI_CHAT_API_KEY"))
    
    parsed_response = None
    try:
        response = generate_content_resilient(
            client=client,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=INDIAN_LAW_SYSTEM_PROMPT,
                temperature=0.2,
                max_output_tokens=4096,
                response_mime_type="application/json",
            ),
            preferred_model=LLM_MODEL
        )
        raw_text = response.text.strip()
        parsed_response = _extract_json(raw_text)
    except Exception as e:
        logger.error(f"Error during ask_document: {e}", exc_info=True)

    if not parsed_response:
        parsed_response = {
            "can_answer": True,
            "final_answer": "Something went wrong on our end, please try again.",
            "confidence": "low"
        }
        
    # 4. Parse output and citations
    can_answer = parsed_response.get("can_answer", True)
    cited_clauses = [str(c['metadata']['chunk_id']) for c in user_chunks]
    cited_statutes = [{"act": c['metadata']['act_name'], "section": str(c['metadata']['section_number'])} for c in statute_chunks]

    user_msg = Conversation(document_id=document_id, role="user", content=request.question)
    db.add(user_msg)

    if not can_answer and not was_last_clarifying:
        clarifying_question = parsed_response.get("clarifying_question", "Could you please clarify your request?")
        bot_msg = Conversation(
            document_id=document_id, 
            role="assistant", 
            content=clarifying_question,
            is_clarifying=True
        )
        db.add(bot_msg)
        db.commit()
        return ChatResponse(
            type="clarification",
            question=clarifying_question,
            cited_clauses=[],
            cited_statutes=[],
            confidence="low"
        )
    else:
        clean_answer = parsed_response.get("final_answer", "")
        confidence = parsed_response.get("confidence", "high").lower()
        if confidence not in ["high", "low"]:
            confidence = "high"
            
        bot_msg = Conversation(
            document_id=document_id, 
            role="assistant", 
            content=clean_answer, 
            cited_clause=str(cited_clauses),
            is_clarifying=False
        )
        db.add(bot_msg)
        db.commit()
        
        return ChatResponse(
            type="answer",
            answer=clean_answer,
            cited_clauses=cited_clauses,
            cited_statutes=cited_statutes,
            confidence=confidence
        )

@router.get("/documents/{document_id}/summary")
def get_document_summary(document_id: str, db: Session = Depends(get_db)):
    """
    Generates a structured summary/checklist from the document's decoded clauses.
    Caches the result in the database.
    """
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    if doc.summary:
        return doc.summary
        
    # Generate summary
    clauses_context = ""
    for c in doc.clauses:
        clauses_context += f"ID: {c.get('id')}\nRisk: {c.get('risk')}\nOriginal: {c.get('original')}\nSimplified: {c.get('simplified')}\nExplanation: {c.get('explanation')}\n\n"
        
    target_lang_name = LANGUAGE_MAP.get(doc.target_language, "English")
    prompt = f"""
--- DOCUMENT CLAUSES ---
{clauses_context}

INSTRUCTIONS:
You are a legal assistant. Generate a summary of this document based strictly on the clauses provided above.
Your output must be in valid JSON format matching exactly this structure:
{{
    "overview": "A one-paragraph plain-English overview of what the document is and its key terms.",
    "checklist": [
        {{
            "question": "A question for the user to ask the other party, derived from 'caution' or 'flag' clauses",
            "cited_clause": "The ID of the clause this relates to (as a string)"
        }}
    ],
    "negotiate": [
        {{
            "clause_summary": "A brief summary of the clause worth negotiating",
            "reason": "A one-line reason why it should be negotiated",
            "cited_clause": "The ID of the clause this relates to (as a string)"
        }}
    ],
    "closing": "If you're unsure about any of this, take this summary to a licensed advocate"
}}

RULES:
1. The `overview` must be written in {target_lang_name}.
2. The `checklist` items must be written in {target_lang_name} and derived ONLY from clauses with risk='caution' or risk='flag'.
3. The `negotiate` items must be written in {target_lang_name} and derived ONLY from clauses with risk='flag'.
4. The `closing` line MUST be exactly: "If you're unsure about any of this, take this summary to a licensed advocate" (translated to {target_lang_name}).
5. DO NOT invent information not present in the clauses.
"""
    client = get_genai_client(api_key=os.environ.get("GEMINI_API_KEY"))
    summary_data = None
    try:
        response = generate_content_resilient(
            client=client,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=INDIAN_LAW_SYSTEM_PROMPT,
                temperature=0.2,
                max_output_tokens=4096,
                response_mime_type="application/json",
            ),
            preferred_model=LLM_MODEL
        )
        raw_text = response.text.strip()
        summary_data = _extract_json(raw_text)
    except Exception as e:
        logger.error(f"Error during summary generation: {e}", exc_info=True)
        raise HTTPException(
            status_code=503,
            detail={"error_code": "llm_unavailable", "message": "Something went wrong on our end, please try again."}
        )
        
    doc.summary = summary_data
    db.commit()
    
    return summary_data

@router.get("/documents/{document_id}/verdict")
def get_document_verdict(document_id: str, db: Session = Depends(get_db)):
    """
    Generates a final verdict on the document based on its clauses.
    """
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    clauses_context = ""
    for c in doc.clauses:
        clauses_context += f"Clause: {c.get('id')}\nRisk: {c.get('risk')}\nOriginal: {c.get('original')}\nSimplified: {c.get('simplified')}\nExplanation: {c.get('explanation')}\n\n"
        
    target_lang_name = LANGUAGE_MAP.get(doc.target_language, "English")
    prompt = f"""
--- DOCUMENT CLAUSES ---
{clauses_context}

INSTRUCTIONS:
You are a legal assistant. Based on the clauses provided above, provide a "Final Verdict" on this legal document.
State whether you recommend signing it, negotiating it, or walking away.
The verdict MUST be very short, punchy, and straight to the point. When referencing specific parts of the document, use the format "Clause X" (e.g. "Clause 1"). Do not use the word "ID".
Write in {target_lang_name}.

Your output must be in valid JSON format matching exactly this structure:
{{
    "verdict": "Your short, straight-to-the-point verdict here."
}}
"""
    client = get_genai_client(api_key=os.environ.get("GEMINI_VERDICT_API_KEY"))
        
    verdict_data = None
    try:
        response = generate_content_resilient(
            client=client,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=INDIAN_LAW_SYSTEM_PROMPT,
                temperature=0.2,
                max_output_tokens=2048,
                response_mime_type="application/json",
            ),
            preferred_model=LLM_MODEL
        )
        raw_text = response.text.strip()
        verdict_data = _extract_json(raw_text)
    except Exception as e:
        logger.error(f"Error during verdict: {e}", exc_info=True)
        raise HTTPException(
            status_code=503,
            detail={"error_code": "llm_unavailable", "message": "Something went wrong on our end, please try again."}
        )
        
    return verdict_data

class TranslateRequest(BaseModel):
    target_language: str

@router.post("/documents/{document_id}/translate")
def translate_document(document_id: str, request: TranslateRequest, db: Session = Depends(get_db)):
    """
    Translates the simplified clauses and explanations of a document into a new target language.
    """
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    if request.target_language not in ["en", "hi", "kn", "ta", "te", "ml", "kok"]:
        raise HTTPException(status_code=400, detail="Unsupported target language.")
        
    # If the document is already in the requested language, return as is
    if doc.target_language == request.target_language:
        return {"clauses": doc.clauses, "target_language": doc.target_language}
        
    clauses_context = ""
    for c in doc.clauses:
        clauses_context += f"ID: {c.get('id')}\nOriginal: {c.get('original')}\nRisk: {c.get('risk')}\n\n"
        
    target_lang_name = LANGUAGE_MAP.get(request.target_language, "English")
    prompt = f"""
You are a legal document analyzer. Translate and simplify the following legal document clauses into {target_lang_name}.
Maintain the exact same "id" and "risk" tag for each clause as provided.

--- DOCUMENT CLAUSES ---
{clauses_context}

For each clause, provide:
1. "id": The exact ID provided.
2. "original": The exact original text provided.
3. "simplified": A plain {target_lang_name} translation/simplification of the clause.
4. "risk": The exact risk tag provided (do not change this).
5. "explanation": A brief explanation of the risk (or why it is safe) in {target_lang_name}.

Respond strictly with a JSON array of these clause objects.
"""
    client = get_genai_client(api_key=os.environ.get("GEMINI_TRANSLATE_API_KEY"))
    
    translated_clauses = None
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
        translated_clauses = _extract_json(raw_text)
    except Exception as e:
        logger.error(f"Error during translation: {e}", exc_info=True)
        raise HTTPException(
            status_code=503,
            detail={"error_code": "llm_unavailable", "message": "Something went wrong on our end, please try again."}
        )
        
    # Update document in DB
    doc.clauses = translated_clauses
    doc.target_language = request.target_language
    doc.summary = None 
    db.commit()
    
    return {"clauses": translated_clauses, "target_language": request.target_language}

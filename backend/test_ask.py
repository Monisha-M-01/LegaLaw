import sys
import os
from dotenv import load_dotenv

sys.path.append(os.path.dirname(__file__))

load_dotenv()

from app.database import Base, engine, SessionLocal, Document
from app.api.endpoints import ask_document, ChatRequest

# Ensure db is created
Base.metadata.create_all(bind=engine)

def run_test():
    print("Setting up dummy document...")
    db = SessionLocal()
    doc_id = "test-doc-123"
    
    # Check if exists, if not create
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        new_doc = Document(
            id=doc_id,
            session_id="test-session",
            filename="dummy_lease.pdf",
            target_language="en",
            clauses=[
                {"chunk_id": 1, "text": "The Lessee shall not assign, sublet, or part with the possession of the demised premises without the prior written consent of the Lessor."}
            ],
            risk_tags={"safe": 1}
        )
        db.add(new_doc)
        db.commit()
    
    # We also need to add a chunk to Chroma for `test-doc-123` so retrieve_relevant_chunks works.
    from app.services.vector_store import store_chunks
    store_chunks(doc_id, [{"chunk_id": 1, "text": "The Lessee shall not assign, sublet, or part with the possession of the demised premises without the prior written consent of the Lessor.", "category": "lease"}])

    print("Document and chunks initialized.")
    
    questions = [
        ("is this legal?", "Ambiguous question"),
        ("Can I rent out my apartment to someone else?", "Clear question")
    ]
    
    for q, desc in questions:
        print(f"\n--- Testing {desc} ---")
        print(f"Asking question: {q}")
        
        request = ChatRequest(
            question=q,
            conversation_history=[],
            target_language="en"
        )
        
        response = ask_document(doc_id, request, db)
        
        print("\nType:", response.type)
        if response.type == "clarification":
            print("Clarification Question:", response.question)
        else:
            print("LLM Answer:", response.answer)
            print("Confidence:", response.confidence)
            print("Cited Clauses:", response.cited_clauses)
            print("Cited Statutes:", response.cited_statutes)
            
    db.close()

if __name__ == "__main__":
    run_test()

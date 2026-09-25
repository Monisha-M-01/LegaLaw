import sys
import os
import json
from dotenv import load_dotenv

sys.path.append(os.path.dirname(__file__))

load_dotenv()

from app.database import Base, engine, SessionLocal, Document
from app.api.endpoints import get_document_summary

# Ensure db is created
Base.metadata.create_all(bind=engine)

def run_test():
    print("Setting up dummy document with varied risk clauses...")
    db = SessionLocal()
    doc_id = "test-doc-summary-123"
    
    # Check if exists, if not create
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        new_doc = Document(
            id=doc_id,
            session_id="test-session-2",
            filename="dummy_lease.pdf",
            target_language="en",
            clauses=[
                {
                    "id": 1, 
                    "original": "The Lessee shall not assign, sublet, or part with the possession of the demised premises without the prior written consent of the Lessor.",
                    "simplified": "You cannot rent out your apartment to someone else (sublet) without getting written permission from your landlord first.",
                    "risk": "safe",
                    "explanation": "This is a standard clause in most leases."
                },
                {
                    "id": 2, 
                    "original": "The Lessor reserves the right to enter the premises at any time without notice for the purpose of inspection or repair.",
                    "simplified": "The landlord can enter your apartment at any time without warning you.",
                    "risk": "flag",
                    "explanation": "In most jurisdictions, landlords are legally required to give 24-48 hours notice before entering, except in emergencies. This clause violates typical tenant privacy rights."
                },
                {
                    "id": 3,
                    "original": "Upon termination of this Agreement, the Lessee shall surrender the premises in the same condition as received, ordinary wear and tear excepted. The Lessee is responsible for professional carpet cleaning upon move-out regardless of condition.",
                    "simplified": "When you move out, you must leave the apartment in the same condition as when you moved in. You also have to pay for professional carpet cleaning, even if they are clean.",
                    "risk": "caution",
                    "explanation": "While returning the apartment in good condition is standard, mandatory professional cleaning charges are sometimes unenforceable depending on local laws."
                }
            ],
            risk_tags={"safe": 1, "caution": 1, "flag": 1}
        )
        db.add(new_doc)
        db.commit()

    print("Calling get_document_summary()...")
    
    try:
        response = get_document_summary(doc_id, db)
        print("\n--- SUMMARY JSON ---")
        print(json.dumps(response, indent=2))
    except Exception as e:
        print("Error:", e)
        
    db.close()

if __name__ == "__main__":
    run_test()

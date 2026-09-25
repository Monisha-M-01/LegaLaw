# AI-Powered Legal Assistant

An AI-powered legal assistant that makes legal documents (rental agreements, loan contracts, ToS) accessible to non-lawyers.

## Core Features
1. Upload a document and get a clause-by-clause plain-English rewrite with risk flags.
2. Ask questions about the document and get answers grounded strictly in retrieved clauses with citations.
3. When a clause is ambiguous or context is missing, asks the user a clarifying question instead of guessing.

## Tech Stack
- **Backend**: FastAPI (Python)
- **Frontend**: React + Vite (Split-pane layout)
- **Vector Store**: ChromaDB (local)
- **Embeddings**: `sentence-transformers` (`all-MiniLM-L6-v2`)
- **LLM**: Google Gemini API
- **Document Parsing**: `pdfplumber` (PDF) and `python-docx` (Word)

## Setup Instructions

### Backend
1. Navigate to the `backend` directory.
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Mac/Linux: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Create a `.env` file in the `backend` directory and add your `GEMINI_API_KEY`.
6. Run the server: `uvicorn app.main:app --reload`

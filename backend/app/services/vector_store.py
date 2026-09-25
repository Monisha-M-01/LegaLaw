import chromadb
from chromadb.config import Settings
from app.config import get_genai_client
import os

# Resolve chroma_data directory relative to the backend package root or cwd
_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_CWD_CHROMA = os.path.join(os.getcwd(), "chroma_data")
_PKG_CHROMA = os.path.join(_BACKEND_DIR, "chroma_data")
CHROMA_PATH = _PKG_CHROMA if os.path.exists(_PKG_CHROMA) else _CWD_CHROMA

# Initialize ChromaDB client with persistent local SQLite storage
chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)

# Create or get the collection for legal documents.
# Explicitly set embedding_function=None because embeddings are generated via Gemini API (gemini-embedding-2).
# This avoids ChromaDB loading heavy ONNX runtime and default models into memory.
collection = chroma_client.get_or_create_collection(
    name="legal_documents",
    embedding_function=None,
    metadata={"hnsw:space": "cosine"} # Use cosine similarity for the embeddings
)

def embed_texts(texts: list[str]) -> list[list[float]]:
    """Generates embeddings for a list of strings."""
    client = get_genai_client()
    if isinstance(texts, str):
        texts = [texts]
    result = client.models.embed_content(
        model="gemini-embedding-2",
        contents=texts
    )
    if hasattr(result, 'embeddings') and isinstance(result.embeddings, list):
        return [e.values for e in result.embeddings]
    return [result.embeddings.values]

def store_chunks(document_id: str, chunks: list[dict]):
    """
    Stores chunks in ChromaDB.
    Expected chunk format: {"chunk_id": int, "text": str, "category": str (optional)}
    """
    if not chunks:
        return
        
    ids = []
    documents = []
    metadatas = []
    
    for chunk in chunks:
        # Create a unique ID for each chunk
        chunk_unique_id = f"{document_id}_chunk_{chunk['chunk_id']}"
        ids.append(chunk_unique_id)
        
        documents.append(chunk["text"])
        
        # Store metadata for filtering and retrieval
        metadata = {
            "document_id": document_id,
            "chunk_id": chunk["chunk_id"]
        }
        if "category" in chunk:
            metadata["category"] = chunk["category"]
            
        metadatas.append(metadata)
        
    # Generate embeddings
    embeddings = embed_texts(documents)
    
    # Upsert into ChromaDB (insert or update)
    collection.upsert(
        ids=ids,
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas
    )

def retrieve_relevant_chunks(query: str, n_results: int = 5, document_id: str = None) -> list[dict]:
    """
    Retrieves the most relevant chunks for a given query.
    Optionally filter by document_id.
    """
    # Guard: ChromaDB raises if the collection is empty or n_results exceeds available count
    total_count = collection.count()
    if total_count == 0:
        return []

    query_embedding = embed_texts([query])[0]

    where_clause = None
    if document_id:
        where_clause = {"document_id": document_id}

    # Clamp n_results to what's actually available to avoid ChromaDB error
    safe_n = min(n_results, total_count)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=safe_n,
        where=where_clause
    )

    retrieved_chunks = []

    # ChromaDB returns lists of lists
    if results['ids'] and len(results['ids'][0]) > 0:
        for i in range(len(results['ids'][0])):
            retrieved_chunks.append({
                "id": results['ids'][0][i],
                "text": results['documents'][0][i],
                "metadata": results['metadatas'][0][i],
                "distance": results['distances'][0][i] if 'distances' in results and results['distances'] else None
            })

    return retrieved_chunks

# --- Statute Reference Dual RAG ---

statute_collection = chroma_client.get_or_create_collection(
    name="statute_reference",
    embedding_function=None,
    metadata={"hnsw:space": "cosine"}
)

def store_statute_chunks(chunks: list[dict]):
    """
    Stores statute section chunks in the statute_reference collection.
    """
    if not chunks:
        return
        
    ids = []
    documents = []
    metadatas = []
    
    for chunk in chunks:
        # e.g., Indian Contract Act_1872_108
        chunk_id = f"{chunk['act_name']}_{chunk['year']}_{chunk['section_number']}"
        # Prevent duplicate ID conflicts if multiple chunks are parsed for the same section
        if chunk_id in ids:
            chunk_id += f"_{len(ids)}"
            
        ids.append(chunk_id)
        documents.append(chunk["text"])
        
        metadatas.append({
            "act_name": chunk["act_name"],
            "section_number": chunk["section_number"],
            "section_title": chunk["section_title"],
            "year": chunk["year"],
            "source_url": chunk["source_url"],
            "code_status": chunk.get("code_status", "current")
        })
        
    embeddings = embed_texts(documents)
    
    statute_collection.upsert(
        ids=ids,
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas
    )

def retrieve_statute_chunks(query: str, n_results: int = 3) -> list[dict]:
    """
    Retrieves the most relevant statute sections for a given query.
    """
    query_embedding = embed_texts([query])[0]

    # Check if collection is empty to avoid query errors
    available_count = statute_collection.count()
    if available_count == 0:
        return []

    # Clamp n_results to what's available to avoid ChromaDB error on small collections
    safe_n = min(n_results, available_count)

    results = statute_collection.query(
        query_embeddings=[query_embedding],
        n_results=safe_n,
        where={"code_status": "current"}
    )
    
    retrieved = []
    if results['ids'] and len(results['ids'][0]) > 0:
        for i in range(len(results['ids'][0])):
            retrieved.append({
                "id": results['ids'][0][i],
                "text": results['documents'][0][i],
                "metadata": results['metadatas'][0][i]
            })
            
    return retrieved

def get_statute_coverage():
    """Returns aggregated metadata of indexed acts."""
    count = statute_collection.count()
    if count == 0:
        return {"total_sections": 0, "acts": []}
        
    # Chroma doesn't have an aggregation API, so we fetch all metadatas
    # For a real scale production app we would store this in SQLite instead.
    all_data = statute_collection.get(include=["metadatas"])
    
    acts_status = {}
    for meta in all_data['metadatas']:
        if meta and "act_name" in meta:
            act = meta["act_name"]
            status = meta.get("code_status", "unknown")
            if act not in acts_status:
                acts_status[act] = status
            
    return {
        "total_sections": count,
        "acts": [{"act_name": k, "code_status": v} for k, v in acts_status.items()]
    }

import re

def chunk_text(text: str) -> list[dict]:
    """
    Splits legal document text into clause-aware chunks.
    Uses regex to identify boundaries like '1.', '1.1', 'Article I', 'Section 1', 
    as well as paragraph breaks.
    """
    
    # Common legal document clause boundary patterns
    # Matches:
    # - "1. ", "1.1 ", "1.1.1 " (Numbered clauses)
    # - "Article 1", "Article I" (Articles)
    # - "Section 1", "Section 1.1" (Sections)
    boundary_pattern = re.compile(
        r'(?:\n|^)\s*(?:'
        r'(?:\d+\.(?:\d+\.)*\s+)'                  # Numbered: 1., 1.1, 1.1.1 
        r'|(?:[A-Z]\.\s+)'                          # Letters: A., B., C.
        r'|(?:Article\s+[IVXLCDM\d]+\s*-?\s*)'      # Article I, Article 1
        r'|(?:Section\s+\d+(?:\.\d+)*\s*-?\s*)'     # Section 1, Section 1.1
        r')', 
        re.IGNORECASE
    )
    
    # Split text using the pattern. We use re.split with a capture group if we wanted to keep the delimiter,
    # but since boundary_pattern above uses non-capturing groups, let's modify it to capture the delimiter
    # so we don't lose the clause numbering.
    
    split_pattern = re.compile(
        r'((?:\n|^)\s*(?:'
        r'\d+\.(?:\d+\.)*\s+'
        r'|[A-Z]\.\s+'
        r'|Article\s+[IVXLCDM\d]+\s*-?\s*'
        r'|Section\s+\d+(?:\.\d+)*\s*-?\s*'
        r'))',
        re.IGNORECASE
    )
    
    parts = split_pattern.split(text)
    
    chunks = []
    current_chunk = ""
    chunk_index = 0
    
    for part in parts:
        if split_pattern.match(part):
            # If current chunk has content, save it before starting a new one
            if current_chunk.strip():
                # We can also do further splitting on double newlines (paragraphs) within large chunks
                sub_chunks = split_by_paragraphs(current_chunk)
                for sc in sub_chunks:
                    if sc.strip():
                        chunks.append({
                            "chunk_id": chunk_index,
                            "text": sc.strip()
                        })
                        chunk_index += 1
                current_chunk = ""
            current_chunk = part
        else:
            current_chunk += part
            
    # Process the last chunk
    if current_chunk.strip():
        sub_chunks = split_by_paragraphs(current_chunk)
        for sc in sub_chunks:
            if sc.strip():
                chunks.append({
                    "chunk_id": chunk_index,
                    "text": sc.strip()
                })
                chunk_index += 1
                
    return chunks

def split_by_paragraphs(text: str) -> list[str]:
    """Splits text by double newlines to isolate paragraphs."""
    # Split by 2 or more newlines
    paragraphs = re.split(r'\n\s*\n', text)
    return [p for p in paragraphs if p.strip()]

from app.services.chunker import chunk_text

def test_chunk_text_basic_numbering():
    text = """
    1. First clause.
    This is the first clause.
    
    1.1 Sub-clause.
    This is a sub-clause.
    
    2. Second clause.
    This is the second clause.
    """
    chunks = chunk_text(text)
    assert len(chunks) == 3
    assert "1. First clause." in chunks[0]["text"]
    assert "1.1 Sub-clause." in chunks[1]["text"]
    assert "2. Second clause." in chunks[2]["text"]

def test_chunk_text_articles():
    text = """
    Article I - Introduction
    This is the introduction.
    
    Article II. Definitions
    These are the definitions.
    """
    chunks = chunk_text(text)
    assert len(chunks) == 2
    assert "Article I" in chunks[0]["text"]
    assert "Article II" in chunks[1]["text"]

def test_chunk_text_paragraphs():
    text = """
    This is a preamble paragraph.
    
    This is another paragraph without a numbered clause.
    """
    chunks = chunk_text(text)
    assert len(chunks) == 2
    assert "This is a preamble paragraph." in chunks[0]["text"]
    assert "another paragraph" in chunks[1]["text"]

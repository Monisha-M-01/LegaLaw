import os
import pdfplumber
import docx

def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from a PDF file using pdfplumber."""
    if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
        raise ValueError("The uploaded PDF file is empty (0 bytes). Please upload a valid document.")
    text = ""
    try:
        with pdfplumber.open(file_path) as pdf:
            if not pdf.pages:
                raise ValueError("The PDF contains no pages.")
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n\n"
    except Exception as e:
        if isinstance(e, ValueError):
            raise
        raise ValueError(f"Unable to parse PDF document: {e}") from e
    return text

def extract_text_from_docx(file_path: str) -> str:
    """Extract text from a DOCX file using python-docx."""
    if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
        raise ValueError("The uploaded DOCX file is empty (0 bytes). Please upload a valid document.")
    try:
        doc = docx.Document(file_path)
        text = ""
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                text += paragraph.text + "\n\n"
    except Exception as e:
        if isinstance(e, ValueError):
            raise
        raise ValueError(f"Unable to parse DOCX document: {e}") from e
    return text

def extract_text_from_document(file_path: str, file_ext: str) -> str:
    """Extract text from a document based on its extension."""
    if file_ext == ".pdf":
        return extract_text_from_pdf(file_path)
    elif file_ext == ".docx":
        return extract_text_from_docx(file_path)
    else:
        raise ValueError(f"Unsupported file extension: {file_ext}")

import os
import requests
import pdfplumber
import re
import sys

# Ensure backend path is in sys.path so we can import app modules
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.services.vector_store import store_statute_chunks, get_statute_coverage

# URLs for Bare Acts from India Code (using direct PDF links if possible, or alternative reliable sources for testing)
STATUTES = [
    {
        "name": "Indian Contract Act",
        "year": "1872",
        "url": "https://lddashboard.legislative.gov.in/sites/default/files/A1872-09.pdf",
        "filename": "A1872-09.pdf",
        "code_status": "current"
    },
    {
        "name": "Model Tenancy Act",
        "year": "2021",
        "url": "https://mohua.gov.in/upload/uploadfiles/files/Model-Tenancy-Act-English-02_06_2021.pdf",
        "filename": "Model-Tenancy-Act-English-02_06_2021.pdf",
        "code_status": "current"
    },
    {
        "name": "Bharatiya Nyaya Sanhita",
        "year": "2023",
        "url": "https://prsindia.org/files/bills_acts/acts_parliament/2023/Bharatiya%20Nyaya%20Sanhita,%202023.pdf",
        "filename": "BNS-2023.pdf",
        "code_status": "current"
    },
    {
        "name": "Bharatiya Nagarik Suraksha Sanhita",
        "year": "2023",
        "url": "https://prsindia.org/files/bills_acts/acts_parliament/2023/Bharatiya%20Nagarik%20Suraksha%20Sanhita,%202023.pdf",
        "filename": "BNSS-2023.pdf",
        "code_status": "current"
    },
    {
        "name": "Constitution of India",
        "year": "1950",
        "url": "https://legislative.gov.in/sites/default/files/COI_English.pdf",
        "filename": "Constitution-1950.pdf",
        "code_status": "current"
    },
    {
        "name": "Indian Penal Code",
        "year": "1860",
        "url": "https://lddashboard.legislative.gov.in/sites/default/files/A1860-45.pdf",
        "filename": "IPC-1860.pdf",
        "code_status": "superseded"
    },
    {
        "name": "Code of Civil Procedure",
        "year": "1908",
        "url": "https://lddashboard.legislative.gov.in/sites/default/files/A1908-05.pdf",
        "filename": "CPC-1908.pdf",
        "code_status": "current"
    },
    {
        "name": "Specific Relief Act",
        "year": "1963",
        "url": "https://lddashboard.legislative.gov.in/sites/default/files/A1963-47.pdf",
        "filename": "SRA-1963.pdf",
        "code_status": "current"
    },
    {
        "name": "Sale of Goods Act",
        "year": "1930",
        "url": "https://lddashboard.legislative.gov.in/sites/default/files/A1930-03.pdf",
        "filename": "SGA-1930.pdf",
        "code_status": "current"
    },
    {
        "name": "Negotiable Instruments Act",
        "year": "1881",
        "url": "https://lddashboard.legislative.gov.in/sites/default/files/A1881-26.pdf",
        "filename": "NIA-1881.pdf",
        "code_status": "current"
    }
]

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "statutes")

def download_pdf(url, filename):
    os.makedirs(DATA_DIR, exist_ok=True)
    filepath = os.path.join(DATA_DIR, filename)
    
    if os.path.exists(filepath):
        print(f"[{filename}] Already exists locally. Skipping download.")
        return filepath
        
    print(f"[{filename}] Downloading from {url}...")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    try:
        response = requests.get(url, headers=headers, stream=True, timeout=10)
        response.raise_for_status()
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"[{filename}] Download complete.")
        return filepath
    except Exception as e:
        print(f"[{filename}] Download failed: {e}")
        return None

def extract_text_from_pdf(filepath):
    text = ""
    try:
        with pdfplumber.open(filepath) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        print(f"Failed to read {filepath}: {e}")
    return text

def chunk_by_section(text, act_name, year, url, code_status="current"):
    """
    Chunks a Bare Act by Section or Article.
    Looks for patterns like "1. Short title..." or "108. Rights and liabilities..."
    For the Constitution, it extracts Parts and Articles.
    """
    chunks = []
    
    if "Constitution" in act_name:
        # Split by Part first to get the Part metadata
        parts = re.split(r'\n(?=PART\s+[IVXLCDM]+\b)', text)
        for part_text in parts:
            part_match = re.match(r'^PART\s+([IVXLCDM]+)\s+(.+?)(?=\n)', part_text)
            part_name = f"PART {part_match.group(1)}" if part_match else "Unknown Part"
            
            # Split part text into Articles
            articles = re.split(r'\n(?=\d+\.\s)', part_text)
            for art in articles:
                art = art.strip()
                if not art: continue
                match = re.match(r'^(\d+)\.\s+([^\n\.\-]+(?:[\.\-][^\n]+)?)', art)
                if match:
                    section_number = match.group(1)
                    section_title = match.group(2).strip()[:100]
                    chunks.append({
                        "act_name": act_name,
                        "section_number": section_number,
                        "section_title": f"{part_name} - {section_title}",
                        "text": art,
                        "year": year,
                        "source_url": url,
                        "code_status": code_status
                    })
        return chunks
        
    # Heuristic regex for Indian Bare Acts sections: Number followed by dot, then title
    # Example: "1. Short title and commencement.-This Act..."
    # We split by the pattern `\n\d+\.\s` 
    
    # Pre-process text to remove common header/footer noises if needed, but let's try direct split first.
    sections_raw = re.split(r'\n(?=\d+\.\s)', text)
    
    # The first element is usually preamble and index. We'll store it as 'Preamble'.
    if sections_raw:
        preamble = sections_raw[0].strip()
        if preamble:
            chunks.append({
                "act_name": act_name,
                "section_number": "Preamble",
                "section_title": "Preamble and Index",
                "text": preamble[:2000], # Keep it bounded if it's huge
                "year": year,
                "source_url": url,
                "code_status": code_status
            })
             
    for sec in sections_raw[1:]:
        sec = sec.strip()
        if not sec:
            continue
            
        # Extract section number and potentially the title
        match = re.match(r'^(\d+)\.\s+([^\n\.\-]+(?:[\.\-][^\n]+)?)', sec)
        if match:
            section_number = match.group(1)
            section_title = match.group(2).strip()
            
            # Clean up title if it grabbed too much body text
            if len(section_title) > 100:
                section_title = section_title[:100] + "..."
                
            chunks.append({
                "act_name": act_name,
                "section_number": section_number,
                "section_title": section_title,
                "text": sec, # Store the full section text
                "year": year,
                "source_url": url,
                "code_status": code_status
            })
        else:
            # If it didn't match cleanly, just treat it as a continuation or generic chunk
            chunks.append({
                "act_name": act_name,
                "section_number": "Unknown",
                "section_title": "Continuation",
                "text": sec,
                "year": year,
                "source_url": url,
                "code_status": code_status
            })
            
    return chunks

def run():
    print("Starting Statute Ingestion...")
    
    for statute in STATUTES:
        text = ""
        filepath = download_pdf(statute["url"], statute["filename"])
        if not filepath:
            print(f"Skipping {statute['name']} download, using fallback mock text.")
            if statute["name"] == "Indian Contract Act":
                text = "1. Short title.-This Act may be called the Indian Contract Act, 1872.\n108. Rights and liabilities of lessor and lessee.-In the absence of a contract or local usage to the contrary, the lessor and the lessee of immoveable property, as against one another, respectively, possess the rights and are subject to the liabilities mentioned in the rules next following, or such of them as are applicable to the property leased."
            elif statute["name"] == "Constitution of India":
                text = "PART III FUNDAMENTAL RIGHTS\n12. Definition.-In this Part, unless the context otherwise requires, the State includes the Government and Parliament of India.\n19. Protection of certain rights regarding freedom of speech etc.-(1) All citizens shall have the right (a) to freedom of speech and expression; (b) to assemble peaceably and without arms; (c) to form associations or unions."
            elif statute["name"] == "Bharatiya Nyaya Sanhita":
                text = "1. Short title, commencement and application.-(1) This Act may be called the Bharatiya Nyaya Sanhita, 2023.\n103. Punishment for murder.-(1) Whoever commits murder shall be punished with death or imprisonment for life, and shall also be liable to fine."
            elif statute["name"] == "Bharatiya Nagarik Suraksha Sanhita":
                text = "1. Short title, extent and commencement.-(1) This Act may be called the Bharatiya Nagarik Suraksha Sanhita, 2023.\n35. Arrest how made.-(1) In making an arrest the police officer or other person making the same shall actually touch or confine the body of the person to be arrested, unless there be a submission to the custody by word or action."
            elif statute["name"] == "Indian Penal Code":
                text = "1. Title and extent of operation of the Code.-This Act shall be called the Indian Penal Code, and shall extend to the whole of India.\n302. Punishment for murder.-Whoever commits murder shall be punished with death, or imprisonment for life, and shall also be liable to fine."
            elif statute["name"] == "Code of Civil Procedure":
                text = "1. Short title, commencement and extent.-This Act may be cited as the Code of Civil Procedure, 1908.\n9. Courts to try all civil suits unless barred.-The Courts shall (subject to the provisions herein contained) have jurisdiction to try all suits of a civil nature excepting suits of which their cognizance is either expressly or impliedly barred."
            elif statute["name"] == "Specific Relief Act":
                text = "1. Short title, extent and commencement.-This Act may be called the Specific Relief Act, 1963.\n10. Specific performance in respect of contracts.-The specific performance of a contract shall be enforced by the court subject to the provisions contained in sub-section (2) of section 11, section 14 and section 16."
            elif statute["name"] == "Sale of Goods Act":
                text = "1. Short title, extent and commencement.-This Act may be called the Sale of Goods Act, 1930.\n4. Sale and agreement to sell.-(1) A contract of sale of goods is a contract whereby the seller transfers or agrees to transfer the property in goods to the buyer for a price."
            elif statute["name"] == "Negotiable Instruments Act":
                text = "1. Short title.-This Act may be called the Negotiable Instruments Act, 1881.\n138. Dishonour of cheque for insufficiency, etc., of funds in the account.-Where any cheque drawn by a person on an account maintained by him with a banker for payment of any amount of money to another person from out of that account for the discharge, in whole or in part, of any debt or other liability, is returned by the bank unpaid, either because of the amount of money standing to the credit of that account is insufficient to honour the cheque or that it exceeds the amount arranged to be paid from that account by an agreement made with that bank, such person shall be deemed to have committed an offence and shall, without prejudice to any other provisions of this Act, be punished with imprisonment for a term which may be extended to two years, or with fine which may extend to twice the amount of the cheque, or with both."
            else:
                text = "1. Short title, extent and commencement.-This Act may be called the Model Tenancy Act, 2021.\n4. Tenancy Agreement.-Notwithstanding anything contained in this Act or any other law for the time being in force, no person shall, after the commencement of this Act, let or take on rent any premises except by an agreement in writing."
        else:
            print(f"Extracting text for {statute['name']}...")
            text = extract_text_from_pdf(filepath)
            
        if not text.strip():
            print(f"No text extracted for {statute['name']}.")
            continue
        
        print(f"Chunking {statute['name']} by section...")
        chunks = chunk_by_section(text, statute["name"], statute["year"], statute["url"], statute.get("code_status", "current"))
        print(f"Created {len(chunks)} chunks.")
        
        print(f"Storing chunks in ChromaDB...")
        store_statute_chunks(chunks)
        print(f"Finished {statute['name']}.\n")
        
    print("Ingestion complete!")
    print("Current Coverage:", get_statute_coverage())

if __name__ == "__main__":
    run()

from pypdf import PdfReader
from typing import List

# constants
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
COLLECTION_NAME = "documents"

def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text from uploaded PDF"""
    reader = PdfReader(file_bytes)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text

def chunk_text(text: str) -> List[str]:
    """Split text into overlapping chunks"""
    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = min(start + CHUNK_SIZE, text_length)
        chunk = text[start:end]
        chunks.append(chunk)
        start += CHUNK_SIZE - CHUNK_OVERLAP

    return chunks

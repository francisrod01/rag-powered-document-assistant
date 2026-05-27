import ollama
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, Distance, VectorParams
from pypdf import PdfReader
import uuid
from typing import List
import os

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

def get_embedding(text: str) -> List[float]:
    """Generate embedding using Ollama"""
    response = ollama.embeddings(model="qwen2:1.5b", prompt=text)
    return response["embedding"]

def ingest_document(file_bytes: bytes, session_id: str, qdrant_client: QdrantClient):
    """Full ingestion pipeline"""
    # Extract text
    text = extract_text_from_pdf(file_bytes)

    # Chunk text
    chunks = chunk_text(text)

    # Create collection if doesn't exist
    collections = qdrant_client.get_collections().collections
    if not any(c.name == COLLECTION_NAME for c in collections):
        embedding_dim = len(get_embedding("test"))
        qdrant_client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=embedding_dim, distance=Distance.COSINE)
        )

    # Generate embeddings and store points
    points = []
    for idx, chunk in enumerate(chunks):
        embedding = get_embedding(chunk)
        point_id = str(uuid.uuid4())
        points.append(
            PointStruct(
                id=point_id,
                vector=embedding,
                payload={
                    "text": chunk,
                    "session_id": session_id,
                    "chunk_index": idx
                }
            )
        )

    qdrant_client.upsert(
        collection_name=COLLECTION_NAME,
        points=points
    )

    return len(chunks)

from io import BytesIO
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, Distance, VectorParams
from pypdf import PdfReader
import uuid
from typing import List

from config import (
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    COLLECTION_NAME,
    EMBEDDING_MODEL,
    EMBEDDING_BATCH_SIZE,
    OLLAMA_HOST,
    OLLAMA_TIMEOUT_SECONDS,
)
from ollama_client import get_embeddings


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text from uploaded PDF"""
    # Wrap bytes in BytesIO to create a file-like object
    pdf_file = BytesIO(file_bytes)
    reader = PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text


def chunk_text(text: str) -> List[str]:
    """Split text into overlapping chunks"""
    if not text.strip():
        return []
    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = min(start + CHUNK_SIZE, text_length)
        chunk = text[start:end]
        if chunk.strip():  # Only add non-empty chunks
            chunks.append(chunk)
        start += CHUNK_SIZE - CHUNK_OVERLAP

    return chunks


def get_embeddings_batch(texts: List[str]) -> List[List[float]]:
    """Get embeddings for a list of texts across Ollama API versions."""
    return get_embeddings(
        OLLAMA_HOST,
        EMBEDDING_MODEL,
        texts,
        timeout=OLLAMA_TIMEOUT_SECONDS,
        batch_size=EMBEDDING_BATCH_SIZE,
    )


def ingest_document(file_bytes: bytes, session_id: str, qdrant_client: QdrantClient):
    """Full ingestion pipeline"""
    # Extract text
    text = extract_text_from_pdf(file_bytes)
    if not text:
        raise ValueError("No text could be extracted from the PDF.")

    # Chunk text
    chunks = chunk_text(text)
    if not chunks:
        raise ValueError("No text chunks were created (document may be empty).")

    # Get embeddings dimension using a test text
    dummy_embedding = get_embeddings_batch(["test"])[0]
    embedding_dim = len(dummy_embedding)

    # Create collection if it doesn't exist
    collections = qdrant_client.get_collections().collections
    if not any(c.name == COLLECTION_NAME for c in collections):
        qdrant_client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=embedding_dim, distance=Distance.COSINE)
        )

    # Batch generate embeddings for all chunks
    embeddings = get_embeddings_batch(chunks)

    # Generate embeddings and store points
    points = []
    for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
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

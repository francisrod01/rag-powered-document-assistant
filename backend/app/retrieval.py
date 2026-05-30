import requests
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
from typing import List, Tuple
from ingestion import OLLAMA_HOST, EMBEDDING_MODEL, COLLECTION_NAME

CHAT_MODEL = "qwen2:1.5b"  # powerful model for answering questions


def get_embedding(text: str) -> List[float]:
    """Get embedding for a single text using Ollama's /api/embed endpoint."""
    response = requests.post(
        f"{OLLAMA_HOST}/api/embed",
        json={"model": EMBEDDING_MODEL, "input": [text]}
    )
    response.raise_for_status()
    return response.json()["embeddings"][0]


def search_similar_chunks(question: str, session_id: str, qdrant_client: QdrantClient, top_k: int = 3) -> List[Tuple[str, float]]:
    """Retrieve top_k relevant chunks for a question"""

    try:
        # Check if collection exists
        collections = qdrant_client.get_collections().collections
        if not any(c.name == COLLECTION_NAME for c in collections):
            return []

        # Get question embedding
        question_embedding = get_embedding(question)

        # Search Qdrant
        search_result = qdrant_client.search(
            collection_name=COLLECTION_NAME,
            query_vector=question_embedding,
            query_filter=Filter(
                must=[FieldCondition(key="session_id", match=MatchValue(value=session_id))]
            ),
            limit=top_k
        )

        # Extract text and scores
        chunks = []
        for point in search_result:
            if point.payload and isinstance(point.payload, dict) and "text" in point.payload:
                chunks.append((point.payload["text"], point.score))
        return chunks
    except Exception as e:
        print(f"Qdrant search error: {e}")
        return []


def generate_answer(question: str, context_chunks: List[Tuple[str, float]]) -> str:
    """Generate answer using Ollama with retrieved context"""
    # Build prompt with context
    context = "\n\n---\n\n".join([chunk[0] for chunk in context_chunks])

    prompt = f"""Ÿou are a helpful assistant answering questions based only on the provided context.

Context:
{context}

Question: {question}

Answer concisely based only on the context above. If the context doesn't contain the answer,
say "I cannot find this information in the document."
"""

    response = requests.post(
        f"{OLLAMA_HOST}/api/generate",
        json={"model": CHAT_MODEL, "prompt": prompt, "max_tokens": 500, "stream": False}
    )
    response.raise_for_status()
    return response.json()["response"].strip()

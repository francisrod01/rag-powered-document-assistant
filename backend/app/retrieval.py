import requests
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
from typing import List, Tuple

from config import OLLAMA_HOST, EMBEDDING_MODEL, COLLECTION_NAME, CHAT_MODEL


def get_embedding(text: str) -> List[float]:
    """Get embedding for a single text using Ollama's /api/embed endpoint."""
    response = requests.post(
        f"{OLLAMA_HOST}/api/embed",
        json={"model": EMBEDDING_MODEL, "input": [text]}
    )
    response.raise_for_status()
    return response.json()["embeddings"][0]


def search_similar_chunks(question: str, session_id: str, qdrant_client: QdrantClient, top_k: int = 10) -> List[Tuple[str, float]]:
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

    prompt = f"""You are a highly logical and precise data extraction assistant. Read the provided Context carefully and answer the Question based ABSOLUTELY ONLY on the Context.

Context:
{context}

Question: {question}

Follow these strict rules:
1. NO HALLUCINATION: Do not invent, guess, or pull in outside knowledge. If the answer is not explicitly in the Context, say: "I cannot find this information in the document."
2. STRICT CONSTRAINTS: If the Question asks for information matching a specific condition (e.g., a certain block of time, a specific technology, or a particular concept), strictly rely on the context to filter and exclude anything that does not match.
3. CLEAR FORMATTING: Group your findings logically. If the Question asks for distinct categories (like courses, patterns, rules, or features), use an ALL CAPS markdown header for each category (e.g., ### PATTERNS).
4. CONCISE LISTS: Use bullet points ("- ") for lists or itemized data. Keep items concise and format them clearly (e.g., "- Concept: Explanation").
5. ENDING: Always end your response exactly with this sentence: "This completes the requested information."

Expected Output Format Example (if categorizing):
### CATEGORY NAME
- Item 1: Brief description based strictly on context.
- Item 2: Brief description.

This completes the requested information.
"""

    response = requests.post(
        f"{OLLAMA_HOST}/api/generate",
        json={
            "model": CHAT_MODEL, 
            "prompt": prompt, 
            "stream": False,
            "options": {
                "temperature": 0.0,
                "top_p": 0.1
            }
        }
    )
    response.raise_for_status()
    return response.json()["response"].strip()

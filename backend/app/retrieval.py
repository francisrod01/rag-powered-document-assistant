import requests
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
from typing import List, Tuple

from config import OLLAMA_HOST, EMBEDDING_MODEL, COLLECTION_NAME, CHAT_MODEL
from ollama_client import get_embeddings


def build_grounded_prompt(question: str, context_chunks: List[Tuple[str, float]]) -> str:
    """Build a retrieval-grounded prompt that allows summarization without hallucination."""
    context = "\n\n---\n\n".join([chunk[0] for chunk in context_chunks])

    return (
        f"You are a precise retrieval-grounded assistant. Answer the Question using ONLY the provided Context.\n\n"
        f"Context:\n{context}\n\n"
        f"Question: {question}\n\n"
        "Rules:\n"
        "1. Use only the Context. Do not add outside facts.\n"
        "2. You MAY summarize, reorganize, and synthesize information that is clearly supported by the Context.\n"
        "3. For broad requests such as summaries, key points, specializations, courses, certifications, responsibilities, or recent work, extract the relevant details from the Context and present them clearly.\n"
        "4. If the Context partially answers the Question, provide the supported part and state briefly what is missing.\n"
        "5. Only say \"I cannot find this information in the document.\" when the Context does not contain relevant information for the Question.\n"
        "6. Prefer concise bullet points for summaries or lists. Use short section headers only when helpful.\n"
        "7. End your response exactly with this sentence: \"This completes the requested information.\""
    )


def get_embedding(text: str) -> List[float]:
    """Get embedding for a single text using Ollama with endpoint compatibility."""
    return get_embeddings(OLLAMA_HOST, EMBEDDING_MODEL, [text])[0]


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
        print(f"Qdrant or embedding error: {e}")
        return []


def generate_answer_stream(question: str, context_chunks: List[Tuple[str, float]]):
    """Generate answer using Ollama with retrieved context and stream response"""
    prompt = build_grounded_prompt(question, context_chunks)

    response = requests.post(
        f"{OLLAMA_HOST}/api/generate",
        json={
            "model": CHAT_MODEL,
            "prompt": prompt,
            "stream": True,
            "keep_alive": "20m",
            "options": {
                "temperature": 0.0,
                "top_p": 0.1,
                "num_ctx": 4096
            }
        },
        stream=True
    )
    response.raise_for_status()
    import json
    for line in response.iter_lines():
        if line:
            yield json.loads(line).get("response", "")

def generate_answer(question: str, context_chunks: List[Tuple[str, float]]) -> str:
    """Generate answer using Ollama with retrieved context"""
    prompt = build_grounded_prompt(question, context_chunks)

    response = requests.post(
        f"{OLLAMA_HOST}/api/generate",
        json={
            "model": CHAT_MODEL,
            "prompt": prompt,
            "stream": False,
            "keep_alive": "20m",
            "options": {
                "temperature": 0.0,
                "top_p": 0.1,
                "num_ctx": 4096
            }
        }
    )
    response.raise_for_status()
    return response.json()["response"].strip()

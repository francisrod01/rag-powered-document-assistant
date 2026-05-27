from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
from typing import List, Tuple
from ingestion import get_embedding, COLLECTION_NAME


def search_similar_chunks(question: str, session_id: str, qdrant_client: QdrantClient, top_k: int = 3) -> List[Tuple[str, float]]:
    """Retrieve top_k relevant chunks for a question"""
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
        chunks.append((point.payload["text"], point.score))

    return chunks

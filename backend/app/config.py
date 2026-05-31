import os
from qdrant_client import QdrantClient

# Environment Configuration
QDRANT_HOST = os.getenv("QDRANT_HOST", "qdrant")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://ollama:11434")

# App Constants
CHUNK_SIZE = 1500
CHUNK_OVERLAP = 100
COLLECTION_NAME = "documents"
EMBEDDING_MODEL = "nomic-embed-text"
CHAT_MODEL = "qwen2:1.5b"

# Singletons
qdrant_client = QdrantClient(host=QDRANT_HOST, port=6333)

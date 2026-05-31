#!/bin/bash
# pull-model.sh - Pull the Qwen2 1.5B model into the running Ollama container

set -e

CONTAINER_NAME="rag-powered-document-assistant-ollama-1"
EMBED_MODEL="nomic-embed-text"
CHAT_MODEL="qwen2:1.5b"

echo "🔍 Checking if Ollama container '$CONTAINER_NAME' is running..."

if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "❌ Container '$CONTAINER_NAME' not found or not running."
    echo "👉 Make sure you've run: docker-compose up -d"
    exit 1
fi

echo "✅ Container found. Pulling models..."
docker exec -it "$CONTAINER_NAME" ollama pull "$EMBED_MODEL"
docker exec -it "$CONTAINER_NAME" ollama pull "$CHAT_MODEL"

echo "🎉 Models are ready!"
echo "You can now use the RAG Assistant."

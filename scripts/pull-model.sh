#!/bin/bash
# pull-model.sh - Pull the Qwen2 1.5B model into the running Ollama container

set -e

CONTAINER_NAME="rag-powered-document-assistant-ollama-1"
MODEL="qwen2:1.5b"

echo "🔍 Checking if Ollama container '$CONTAINER_NAME' is running..."

if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "❌ Container '$CONTAINER_NAME' not found or not running."
    echo "👉 Make sure you've run: docker-compose up -d"
    exit 1
fi

echo "✅ Container found. Pulling model '$MODEL'..."
docker exec -it "$CONTAINER_NAME" ollama pull "$MODEL"

echo "🎉 Model '$MODEL' is ready!"
echo "You can now use the RAG Assistant."

# RAG-powered Document Assistant

This is an interactive app where you can upload a PDF and then ask questions in natural language.  
For example, upload a technical report and get answers instantly, with citations.

### ✨ Features
- **Local LLM RAG Pipeline**: Fully private workflow without external API dependencies.
- **Real-Time Text Streaming**: Answers stream seamlessly chunk-by-chunk just like ChatGPT for a highly responsive UX.
- **Session Chat History**: Contextual message history is saved within SQLite to keep track of your sessions.

![App Preview](docs/screenshots/rag_powered_project_preview.png)

Author: [Francis Batista](https://github.com/francisrod01)


## 🏗 Architecture

This assistant uses a Retrieval-Augmented Generation (RAG) architecture:
1. **Frontend**: Streamlit provides a simple UI to upload PDFs and natively handles real-time response streaming.
2. **Backend**: A FastAPI server coordinates ingestion, retrieval, and serves responses incrementally via an NDJSON streaming endpoint (`/ask_stream`).
3. **Storage**: Qdrant Vector Database stores document embeddings, and local SQLite tracks user chat histories.
4. **LLM Engine**: Ollama runs models locally (`nomic-embed-text` for embeddings, `qwen2:1.5b` for generation).

## 📁 Project Structure

```text
rag-powered-document-assistant/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── ingestion.py
│   │   ├── retrieval.py
│   │   └── models.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── app.py
│   ├── requirements.txt
│   └── Dockerfile
├── docker-compose.yml
└── .env
```


## 🚀 Quick Start Commands

```bash
cd project-folder

# Start all containers
docker compose up  -d --build

# Pull the AI models for Ollama to use
docker exec -it rag-powered-document-assistant-ollama-1 ollama pull nomic-embed-text
docker exec -it rag-powered-document-assistant-ollama-1 ollama pull qwen2:1.5b

# Alternatively, you can use the make command or provided scripts:
# make pull-model
```

Open your browser to check it out
- Frontend: http://localhost:8501
- API docs: http://localhost:8000/docs


## ✅ Test It

### Using the Web UI
* Upload a PDF (any report, article, or book chapter)
* Wait for "Processing" to complete
* Ask questions like:
  - "What is the main topic of this document?"
  - "Summarise the key points"
  - "What does the document say about [specific term]"
* Watch the answer output stream progressively chunk-by-chunk on the screen.

### Testing the Delivery Stream via Terminal
If you want to view how the NDJSON response delivers chunks incrementally, you can execute our Python test script:
```bash
# From the project root, run the streaming tester
python backend/tests/test_stream_api.py
```


## 🔧 Troubleshooting

| Issue | Fix |
|---|---|
| Ollama connection refused | Wait 10 seconds after `docker-compose up`, then pull model |
| Qdrant collection error | Delete volume: `docker-compose down -v`, then restart |
| Slow responses | Reduce CHUNK_SIZE in `ingestion.py` to 300 |
| Memory issues | Add to docker-compose: `deploy:` -> `resources:` -> `limits:` -> `memory: 2G` |


## License

Apache License 2.0

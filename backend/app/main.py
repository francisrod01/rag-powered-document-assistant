from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from qdrant_client import QdrantClient
import os
from models import QuestionRequest, QuestionResponse, UploadResponse
from ingestion import ingest_document
from retrieval import search_similar_chunks, generate_answer

app = FastAPI(title="RAG-powered Assistant API")


# CORS for Streamlit frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Qdrant client
qdrant_client = QdrantClient(
    host=os.getenv("QDRANT_HOST", "qdrant"),
    port=6333
)


@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/upload/{session_id}", response_model=UploadResponse)
async def upload_document(session_id: str, file: UploadFile = File(...)):
    """Upload and ingest a PDF document"""
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    try:
        contents = await file.read()
        chunk_count = ingest_document(contents, session_id, qdrant_client)
        return UploadResponse(
            message=f"Successfully ingested {file.filename}",
            chunk_count=chunk_count,
            session_id=session_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")


@app.post("/ask", response_model=QuestionResponse)
async def ask_question(request: QuestionRequest):
    """Ask a question about uploaded documents"""
    try:
        # Search for relevant chunks
        relevant_chunks = search_similar_chunks(
            request.question,
            request.session_id,
            qdrant_client
        )

        if not relevant_chunks:
            return QuestionResponse(
                answer="No documents found for this session. Please upload a PDF first.",
                sources=[]
            )

        # Generate answer
        answer = generate_answer(request.question, relevant_chunks)

        # Extract source texts
        sources = [chunk[0][:200] + "..." for chunk in relevant_chunks]

        return QuestionResponse(answer=answer, sources=sources)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating answer: {str(e)}")

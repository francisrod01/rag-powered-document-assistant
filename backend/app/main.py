from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
import json
import hashlib

from database import engine, Base, get_db
from models import QuestionRequest, QuestionResponse, UploadResponse, ChatMessage, ChatMessageResponse, SessionResponse, DocumentHash
from ingestion import ingest_document
from fastapi.responses import StreamingResponse
from retrieval import search_similar_chunks, generate_answer, generate_answer_stream
from config import qdrant_client

# Create DB tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="RAG-powered Assistant API")


# CORS for Streamlit frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/upload/{session_id}", response_model=UploadResponse)
async def upload_document(session_id: str, file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload and ingest a PDF document"""
    if not file.filename or not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be a PDF with a valid filename")

    try:
        contents = await file.read()

        # Check if file has already been ingested using SHA-256 hash
        file_hash = hashlib.sha256(contents).hexdigest()
        existing_doc = db.query(DocumentHash).filter(
            DocumentHash.session_id == session_id,
            DocumentHash.file_hash == file_hash
        ).first()

        if existing_doc is not None:
            return UploadResponse(
                message="It seems that this file was previously uploaded",
                chunk_count=0,
                session_id=session_id
            )

        # Process and ingest
        chunk_count = ingest_document(contents, session_id, qdrant_client)

        # Save to database to prevent re-ingestion
        db.add(DocumentHash(session_id=session_id, file_hash=file_hash, filename=file.filename))
        db.commit()

        return UploadResponse(
            message=f"Successfully ingested {file.filename}",
            chunk_count=chunk_count,
            session_id=session_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")


@app.post("/ask_stream")
async def ask_question_stream(request: QuestionRequest, db: Session = Depends(get_db)):
    """Ask a question about uploaded documents with streaming response"""
    relevant_chunks = search_similar_chunks(
        request.question,
        request.session_id,
        qdrant_client
    )

    import re
    import json

    if not relevant_chunks:
        answer = "No documents found for this session. Please upload a PDF first."
        sources = []
    else:
        answer = None
        sources = [re.sub(r'\s+', ' ', chunk[0]).strip()[:200] + "..." for chunk in relevant_chunks]

    def generator():
        full_answer = ""
        if answer:
            full_answer = answer
            yield json.dumps({"chunk": full_answer}) + "\n"
        else:
            for chunk in generate_answer_stream(request.question, relevant_chunks):
                full_answer += chunk
                yield json.dumps({"chunk": chunk}) + "\n"

        yield json.dumps({"sources": sources}) + "\n"

        try:
            user_msg = ChatMessage(
                session_id=request.session_id,
                role="user",
                content=request.question,
                sources=None
            )
            db.add(user_msg)

            assistant_msg = ChatMessage(
                session_id=request.session_id,
                role="assistant",
                content=full_answer,
                sources=json.dumps(sources) if sources else None
            )
            db.add(assistant_msg)
            db.commit()
        except Exception as e:
            pass

    return StreamingResponse(generator(), media_type="application/x-ndjson")


@app.post("/ask", response_model=QuestionResponse)
async def ask_question(request: QuestionRequest, db: Session = Depends(get_db)):
    """Ask a question about uploaded documents"""
    try:
        # Search for relevant chunks
        relevant_chunks = search_similar_chunks(
            request.question,
            request.session_id,
            qdrant_client
        )

        if not relevant_chunks:
            answer = "No documents found for this session. Please upload a PDF first."
            sources = []
        else:
            # Generate answer
            answer = generate_answer(request.question, relevant_chunks)

            import re

            # Extract source texts and clean up formatting
            # Replaces all consecutive whitespaces/newlines with a single space
            sources = [re.sub(r'\s+', ' ', chunk[0]).strip()[:200] + "..." for chunk in relevant_chunks]

        # Save User Message to DB
        user_msg = ChatMessage(
            session_id=request.session_id,
            role="user",
            content=request.question,
            sources=None
        )
        db.add(user_msg)

        # Save Assistant Message to DB
        assistant_msg = ChatMessage(
            session_id=request.session_id,
            role="assistant",
            content=answer,
            sources=json.dumps(sources) if sources else None
        )
        db.add(assistant_msg)
        db.commit()

        return QuestionResponse(answer=answer, sources=sources)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating answer: {str(e)}")


@app.get("/sessions", response_model=List[SessionResponse])
async def get_sessions(db: Session = Depends(get_db)):
    """Get all past chat sessions"""
    # Group by session_id and get the max created_at
    sessions = db.query(
        ChatMessage.session_id,
        func.max(ChatMessage.created_at).label('last_active')
    ).group_by(ChatMessage.session_id).order_by(func.max(ChatMessage.created_at).desc()).all()

    return [SessionResponse(session_id=s.session_id, last_active=s.last_active) for s in sessions]


@app.get("/history/{session_id}", response_model=List[ChatMessageResponse])
async def get_history(session_id: str, db: Session = Depends(get_db)):
    """Get chat history for a given session"""
    messages = db.query(ChatMessage).filter(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at.asc()).all()
    return [
        ChatMessageResponse(
            role=msg.role,
            content=msg.content,
            sources=msg.get_sources_list(),
            created_at=msg.created_at
        ) for msg in messages
    ]

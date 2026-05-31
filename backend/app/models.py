from pydantic import BaseModel, ConfigDict
from typing import List, Optional
import datetime
import json
from sqlalchemy import String, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column
from database import Base

# SQLAlchemy Models
class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    session_id: Mapped[str] = mapped_column(String, index=True)
    role: Mapped[str] = mapped_column(String)  # 'user' or 'assistant'
    content: Mapped[str] = mapped_column(Text)
    sources: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Store JSON representation of list
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=lambda: datetime.datetime.now(datetime.UTC))

    def get_sources_list(self) -> List[str]:
        val = getattr(self, "sources", None)
        if val is not None and isinstance(val, str) and val.strip():
            return json.loads(val)
        return []

class DocumentHash(Base):
    __tablename__ = "document_hashes"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    session_id: Mapped[str] = mapped_column(String, index=True)
    file_hash: Mapped[str] = mapped_column(String, index=True)
    filename: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=lambda: datetime.datetime.now(datetime.UTC))

# Pydantic Models for API
class QuestionRequest(BaseModel):
    question: str
    session_id: str

class QuestionResponse(BaseModel):
    answer: str
    sources: List[str]

class UploadResponse(BaseModel):
    message: str
    chunk_count: int
    session_id: str

class ChatMessageResponse(BaseModel):
    role: str
    content: str
    sources: Optional[List[str]] = None
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)

class SessionResponse(BaseModel):
    session_id: str
    last_active: datetime.datetime

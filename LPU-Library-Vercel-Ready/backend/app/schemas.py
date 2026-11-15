from pydantic import BaseModel, Field
from typing import Optional

class ChatRequest(BaseModel):
    question: str = Field(min_length=2, max_length=4000)
    conversation_id: Optional[str] = None

class Source(BaseModel):
    document: str
    page: Optional[int] = None
    chunk_id: str
    book_id: Optional[str] = None
    title: Optional[str] = None
    author: Optional[str] = None
    excerpt: str

class ChatResponse(BaseModel):
    conversation_id: str
    answer: str
    sources: list[Source]
    retrieval_count: int
    grounded: bool

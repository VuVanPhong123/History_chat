from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# Xóa AdminConfig class vì không còn dùng nữa

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[int] = None

class ChatResponse(BaseModel):
    session_id: int
    message: str

class QuizRequest(BaseModel):
    topic: str
    num_questions: int = 10
    topic_ids: Optional[List[int]] = None

class QuizQuestionOutput(BaseModel):
    question: str
    options: List[str]
    correct_answer: str
    explanation: str
    source_id: int

class QuizResponse(BaseModel):
    test_id: int
    questions: List[QuizQuestionOutput]

class MessageHistory(BaseModel):
    id: int
    session_id: int
    role: str
    content: str
    timestamp: datetime

class ChatSessionOutput(BaseModel):
    id: int
    title: str
    created_at: datetime
    messages: List[MessageHistory] = []

class ChatStreamChunk(BaseModel):
    chunk: str
    session_id: int
    status: str = "streaming"

class ChatResponse(BaseModel):
    session_id: int
    message: str
    status: str = "completed"
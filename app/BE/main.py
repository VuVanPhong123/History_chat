from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
import requests
import time
import uuid
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="History ChatBot Local API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Config
KAGGLE_SERVER_URL = os.getenv("KAGGLE_SERVER_URL")

class ChatRequest(BaseModel):
    question: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    answer: str
    session_id: str
    processing_time: float

# In-memory storage (có thể thay bằng database sau)
conversations = {}

class KaggleClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        
    def health_check(self) -> bool:
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            return response.status_code == 200
        except:
            return False
            
    def generate_answer(self, question: str, session_id: str) -> dict:
        try:
            response = requests.post(
                f"{self.base_url}/chat",
                json={
                    "question": question,
                    "session_id": session_id
                },
                timeout=60
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise HTTPException(status_code=503, detail=f"Kaggle server error: {str(e)}")

def get_kaggle_client():
    return KaggleClient(KAGGLE_SERVER_URL)

@app.get("/")
async def root():
    return {"message": "History ChatBot Local API", "status": "running"}

@app.get("/health")
async def health_check(client: KaggleClient = Depends(get_kaggle_client)):
    local_health = {"local": "healthy"}
    kaggle_health = {"kaggle": "healthy" if client.health_check() else "unreachable"}
    return {**local_health, **kaggle_health}

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest, client: KaggleClient = Depends(get_kaggle_client)):
    start_time = time.time()
    
    session_id = request.session_id or str(uuid.uuid4())
    if session_id not in conversations:
        conversations[session_id] = []
    
    if not client.health_check():
        raise HTTPException(
            status_code=503, 
            detail="Kaggle model server is unavailable. Please check if the Kaggle notebook is running."
        )
    
    try:
        kaggle_response = client.generate_answer(request.question, session_id)
        
        conversations[session_id].append({
            "question": request.question,
            "answer": kaggle_response["answer"],
            "timestamp": time.time(),
            "processing_time": kaggle_response["processing_time"]
        })
        
        total_processing_time = time.time() - start_time
        
        return ChatResponse(
            answer=kaggle_response["answer"],
            session_id=session_id,
            processing_time=total_processing_time
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/sessions")
async def get_sessions():
    return {"sessions": list(conversations.keys())}

@app.get("/api/session/{session_id}/messages")
async def get_session_messages(session_id: str):
    if session_id not in conversations:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"messages": conversations[session_id]}

# Serve frontend
app.mount("/", StaticFiles(directory="../frontend", html=True), name="frontend")

@app.get("/favicon.ico")
async def favicon():
    return FileResponse("../frontend/favicon.ico")

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Local History ChatBot...")
    print(f"📡 Kaggle Server: {KAGGLE_SERVER_URL}")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
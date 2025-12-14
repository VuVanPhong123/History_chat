from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.config import settings
from app.database import engine, Base
from app.core.rag_store import rag_store
from app.routers import auth, admin, chat, quiz
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager cho startup/shutdown events"""
    
    logger.info(" Starting History Chat & Quiz Proxy Server...")
    
    try:
        Base.metadata.create_all(bind=engine)
        logger.info(" Database tables created")
    except Exception as e:
        logger.error(f" Database error: {e}")
    
    try:
        await rag_store.load()
        logger.info(f" RAG data loaded: {len(rag_store.data)} entries")
    except Exception as e:
        logger.error(f" RAG data loading error: {e}")
    
    # Log worker status
    logger.info(f" Chat Workers configured: {len(settings.chat_worker_urls)} URLs")
    logger.info(f" Quiz Workers configured: {len(settings.quiz_worker_urls)} URLs")
    
    if not settings.chat_worker_urls:
        logger.warning(" No chat workers configured! Chat functionality will not work.")
    
    if not settings.quiz_worker_urls:
        logger.warning(" No quiz workers configured! Quiz functionality will not work.")
    
    yield
    
    logger.info(" Shutting down...")

app = FastAPI(
    title="History Chat & Quiz Proxy Server",
    description="Proxy server for AI-powered history chat and quiz generation",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Thêm prefix cho tất cả routers
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(quiz.router, prefix="/api/quiz", tags=["quiz"])

@app.get("/")
async def root():
    return {
        "message": "History Chat & Quiz Proxy Server",
        "status": "running",
        "docs": "/docs",
        "redoc": "/redoc",
        "environment": settings.environment,
        "workers_configured": {
            "chat_workers": len(settings.chat_worker_urls),
            "quiz_workers": len(settings.quiz_worker_urls)
        },
        "quiz_topics": {
            "total": 15,
            "range": "1-15",
            "note": "Frontend should map topic IDs to names"
        }
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "rag_loaded": rag_store.loaded,
        "rag_count": len(rag_store.data) if rag_store.loaded else 0,
        "database": "connected",
        "workers": {
            "chat": len(settings.chat_worker_urls),
            "quiz": len(settings.quiz_worker_urls)
        }
    }

@app.get("/info")
async def server_info():
    return {
        "server": "FastAPI",
        "port": settings.server_port,
        "environment": settings.environment,
        "frontend_url": settings.frontend_url,
        "workers": {
            "chat_urls": settings.chat_worker_urls,
            "quiz_urls": settings.quiz_worker_urls
        }
    }

@app.get("/api/test")
async def test_api():
    return {"message": "API is working!"}

@app.get("/api/chat/test")
async def test_chat_api():
    return {"message": "Chat API endpoint is working!"}

@app.get("/api/quiz/test")
async def test_quiz_api():
    return {"message": "Quiz API endpoint is working!"}
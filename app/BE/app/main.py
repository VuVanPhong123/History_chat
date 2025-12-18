from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.config import settings
from app.database import engine, Base
from app.core.rag_store import rag_store
from app.core.worker_manager import worker_manager
from app.routers import auth, admin, chat, quiz
import logging
import threading
import time
import psutil
import os

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def cleanup_stale_connections_periodically():
    """Periodically clean up stale connections"""
    while True:
        try:
            stale_count = worker_manager.cleanup_stale_connections(timeout_seconds=300)
            if stale_count > 0:
                logger.warning(f"Cleaned up {stale_count} stale connections")
        except Exception as e:
            logger.error(f"Error in cleanup thread: {e}")
        time.sleep(60)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting History Chat & Quiz Proxy Server...")
    
    try:
        await rag_store.load() 
        logger.info("RAG Store loaded successfully")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created")
    except Exception as e:
        logger.error(f"Database error: {e}")
    
    try:
        await rag_store.load()
        logger.info(f"RAG data loaded: {len(rag_store.data)} entries")
    except Exception as e:
        logger.error(f"RAG data loading error: {e}")
    
    logger.info(f"Chat Workers configured: {len(settings.chat_worker_urls)} URLs")
    logger.info(f"Quiz Workers configured: {len(settings.quiz_worker_urls)} URLs")
    
    if not settings.chat_worker_urls:
        logger.warning("No chat workers configured! Chat functionality will not work.")
    
    if not settings.quiz_worker_urls:
        logger.warning("No quiz workers configured! Quiz functionality will not work.")
    
    cleanup_thread = threading.Thread(
        target=cleanup_stale_connections_periodically,
        daemon=True,
        name="ConnectionCleanup"
    )
    cleanup_thread.start()
    logger.info("Started connection cleanup thread")
    
    yield
    
    logger.info("Shutting down...")

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

@app.get("/api/monitor/connections")
async def monitor_connections():
    return worker_manager.get_status()

@app.get("/api/monitor/system")
async def monitor_system():
    try:
        cpu_percent = psutil.cpu_percent(interval=0.5)
        memory = psutil.virtual_memory()
        
        return {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_used_mb": round(memory.used / (1024 * 1024), 2),
            "memory_total_mb": round(memory.total / (1024 * 1024), 2),
            "active_threads": threading.active_count(),
            "active_connections": len(worker_manager.active_connections),
            "process_id": os.getpid(),
            "uptime_seconds": time.time() - psutil.Process(os.getpid()).create_time()
        }
    except Exception as e:
        logger.error(f"Error getting system info: {e}")
        return {"error": str(e)}

@app.get("/api/monitor/logs")
async def get_recent_logs(lines: int = 50):
    try:
        log_file = "server.log"
        if os.path.exists(log_file):
            with open(log_file, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
                recent_lines = all_lines[-lines:] if lines > 0 else all_lines
                return {
                    "log_file": log_file,
                    "total_lines": len(all_lines),
                    "recent_lines": recent_lines
                }
        else:
            return {"message": "Log file not found", "log_file": log_file}
    except Exception as e:
        logger.error(f"Error reading log file: {e}")
        return {"error": str(e)}

@app.get("/api/test")
async def test_api():
    return {"message": "API is working!"}

@app.get("/api/chat/test")
async def test_chat_api():
    return {"message": "Chat API endpoint is working!"}

@app.get("/api/quiz/test")
async def test_quiz_api():
    return {"message": "Quiz API endpoint is working!"}
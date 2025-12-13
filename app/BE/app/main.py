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
    
    yield
    
    logger.info(" Shutting down...")

app = FastAPI(
    title="History Chat & Quiz Proxy Server",
    description="Proxy server for AI-powered history chat and quiz generation (Localhost)",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  
        "https://your-vercel-app.vercel.app",  
        "https://*.vercel.app"  
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth")
app.include_router(admin.router, prefix="/api/admin")
app.include_router(chat.router, prefix="/api/chat")
app.include_router(quiz.router, prefix="/api/quiz")

@app.get("/")
async def root():
    return {
        "message": "History Chat & Quiz Proxy Server",
        "status": "running",
        "docs": "/docs",
        "redoc": "/redoc",
        "environment": settings.environment
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "rag_loaded": rag_store.loaded,
        "rag_count": len(rag_store.data) if rag_store.loaded else 0,
        "database": "connected"
    }

@app.get("/info")
async def server_info():
    return {
        "server": "FastAPI",
        "port": settings.server_port,
        "environment": settings.environment,
        "frontend_url": settings.frontend_url
    }
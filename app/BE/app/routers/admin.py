from fastapi import APIRouter, Depends, HTTPException
from app.core.worker_manager import worker_manager
from app.dependencies import get_current_admin

router = APIRouter(tags=["admin"])

@router.get("/status")
async def get_status(current_admin: str = Depends(get_current_admin)):
    """Lấy trạng thái hiện tại của workers (chỉ xem)"""
    return {
        "chat_workers": worker_manager.chat_worker_urls,
        "quiz_workers": worker_manager.quiz_worker_urls,
        "total_chat_workers": len(worker_manager.chat_worker_urls),
        "total_quiz_workers": len(worker_manager.quiz_worker_urls),
        "note": "Worker URLs are configured in .env file. To change, update CHAT_WORKER_URLS and QUIZ_WORKER_URLS and restart server."
    }
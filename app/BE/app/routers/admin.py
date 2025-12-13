from fastapi import APIRouter, Depends, HTTPException
from app import schemas
from app.core.worker_manager import worker_manager
from app.dependencies import get_current_admin

router = APIRouter(tags=["admin"])

@router.post("/config")
async def update_config(
    config: schemas.AdminConfig,
    current_admin: str = Depends(get_current_admin)
):
    """Cập nhật URLs của workers (cần admin token)"""
    worker_manager.update_chat_workers(config.chat_worker_urls)
    worker_manager.update_quiz_workers(config.quiz_worker_urls)
    
    return {
        "message": "Configuration updated successfully",
        "chat_workers": len(config.chat_worker_urls),
        "quiz_workers": len(config.quiz_worker_urls)
    }

@router.get("/status")
async def get_status(current_admin: str = Depends(get_current_admin)):
    """Lấy trạng thái hiện tại của workers"""
    return {
        "chat_workers": worker_manager.chat_worker_urls,
        "quiz_workers": worker_manager.quiz_worker_urls,
        "total_chat_workers": len(worker_manager.chat_worker_urls),
        "total_quiz_workers": len(worker_manager.quiz_worker_urls)
    }
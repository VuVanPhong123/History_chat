from fastapi import APIRouter, Depends, HTTPException
from app import schemas, crud
from app.core.worker_manager import worker_manager
from app.database import get_db
from sqlalchemy.orm import Session

router = APIRouter(tags=["chat"])

@router.post("/chat", response_model=schemas.ChatResponse)
async def chat(
    request: schemas.ChatRequest,
    db: Session = Depends(get_db)
):

    user = crud.get_user(db, user_id=1)
    if not user:
        user = crud.create_user(db, username="default_user")
    
    if request.session_id is None:
        session = crud.create_chat_session(db, user_id=user.id, title=request.message[:50])
    else:
        session = crud.get_chat_session(db, request.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
    
    crud.create_message(db, session_id=session.id, role="user", content=request.message)
    
    try:
        worker_url = worker_manager.get_chat_worker()
        response_text = await worker_manager.call_chat_worker(worker_url, request.message)
    except HTTPException as e:
        response_text = f"Error: {e.detail}"
    
    crud.create_message(db, session_id=session.id, role="assistant", content=response_text)
    
    return schemas.ChatResponse(
        session_id=session.id,
        message=response_text
    )

@router.get("/sessions")
async def get_sessions(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Lấy danh sách chat sessions"""
    user = crud.get_user(db, user_id=1)
    if not user:
        return []
    
    sessions = crud.get_chat_sessions(db, user_id=user.id, skip=skip, limit=limit)
    
    result = []
    for session in sessions:
        messages = crud.get_chat_messages(db, session_id=session.id, limit=1)
        result.append({
            "id": session.id,
            "title": session.title,
            "created_at": session.created_at,
            "last_message": messages[0].content if messages else ""
        })
    
    return result

@router.get("/sessions/{session_id}/messages")
async def get_session_messages(
    session_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    session = crud.get_chat_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    messages = crud.get_chat_messages(db, session_id=session_id, skip=skip, limit=limit)
    
    return [
        {
            "id": msg.id,
            "role": msg.role,
            "content": msg.content,
            "timestamp": msg.timestamp
        }
        for msg in messages
    ]
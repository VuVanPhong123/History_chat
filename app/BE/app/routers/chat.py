from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
import json
import httpx
from app import schemas, crud
from app.core.worker_manager import worker_manager
from app.database import get_db
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["chat"])

@router.post("/")
async def chat(
    request: schemas.ChatRequest,
    db: Session = Depends(get_db)
):
    print(f"[Chat] Nhận request: {request.message}, session_id: {request.session_id}")
    
    user = crud.get_user(db, user_id=1)
    if not user:
        user = crud.create_user(db, username="default_user")
    
    if request.session_id is None:
        session = crud.create_chat_session(db, user_id=user.id, title=request.message[:50])
        session_id_for_worker = str(session.id)  # Chuyển thành string
    else:
        session = crud.get_chat_session(db, request.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        session_id_for_worker = str(session.id)  # Chuyển thành string
    
    crud.create_message(db, session_id=session.id, role="user", content=request.message)
    
    try:
        worker_url = worker_manager.get_chat_worker()
        print(f"[Chat] Gọi worker: {worker_url}")
        
        async def generate_stream():
            full_response = ""
            try:
                # Debug: in request trước khi gửi
                request_body = {
                    "question": request.message,
                    "session_id": session_id_for_worker  # Đã là string
                }
                print(f"[Chat] Request body gửi đến worker: {request_body}")
                
                # Gọi worker với streaming
                async with httpx.AsyncClient(timeout=60.0) as client:
                    # Thử gửi request test trước để debug
                    try:
                        test_response = await client.post(
                            f"{worker_url}/chat",
                            json=request_body,
                            headers={"Content-Type": "application/json"}
                        )
                        print(f"[Chat] Test response status: {test_response.status_code}")
                        if test_response.status_code != 200:
                            print(f"[Chat] Test response body: {test_response.text}")
                    except Exception as e:
                        print(f"[Chat] Test request error: {e}")
                    
                    # Gọi streaming
                    async with client.stream(
                        "POST",
                        f"{worker_url}/chat",
                        json=request_body,
                        headers={"Content-Type": "application/json"}
                    ) as response:
                        print(f"[Chat] Stream response status: {response.status_code}")
                        response.raise_for_status()
                        
                        async for line in response.aiter_lines():
                            if line.strip():
                                try:
                                    data = json.loads(line)
                                    print(f"[Chat] Nhận chunk từ worker: {data.keys()}")
                                    
                                    if "text" in data:
                                        chunk = data["text"]
                                        full_response += chunk
                                        yield json.dumps({
                                            "chunk": chunk,
                                            "session_id": session.id,
                                            "status": "streaming"
                                        }) + "\n"
                                    elif "error" in data:
                                        print(f"[Chat] Worker error: {data['error']}")
                                        raise Exception(data["error"])
                                except json.JSONDecodeError as e:
                                    print(f"[Chat] JSON decode error: {e}, line: {line}")
                                    continue
                
                # Lưu tin nhắn hoàn chỉnh vào database
                crud.create_message(db, session_id=session.id, role="assistant", content=full_response)
                
                yield json.dumps({
                    "session_id": session.id,
                    "message": full_response,
                    "status": "completed"
                }) + "\n"
                
            except httpx.HTTPStatusError as e:
                print(f"[Chat] HTTP error: {e.response.status_code} - {e.response.text}")
                error_msg = f"Worker error: {e.response.status_code}"
                yield json.dumps({
                    "session_id": session.id,
                    "message": error_msg,
                    "status": "error"
                }) + "\n"
                crud.create_message(db, session_id=session.id, role="assistant", content=error_msg)
            except Exception as e:
                print(f"[Chat] Error in chat stream: {e}")
                error_msg = f"Error: {str(e)}"
                yield json.dumps({
                    "session_id": session.id,
                    "message": error_msg,
                    "status": "error"
                }) + "\n"
                crud.create_message(db, session_id=session.id, role="assistant", content=error_msg)
        
        return StreamingResponse(generate_stream(), media_type="application/x-ndjson")
        
    except HTTPException as e:
        print(f"[Chat] HTTPException: {e.detail}")
        return {"session_id": session.id if 'session' in locals() else 0, "message": f"Error: {e.detail}", "status": "error"}
    except Exception as e:
        print(f"[Chat] System error: {e}")
        return {"session_id": session.id if 'session' in locals() else 0, "message": f"System error: {str(e)}", "status": "error"}
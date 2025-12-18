from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
import json
import httpx
import time
import asyncio
import logging
from app import schemas, crud
from app.core.worker_manager import worker_manager
from app.database import get_db
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter(tags=["chat"])

def log_stream_status(session_id, worker_url, status, details=""):
    logger.info(f"[STREAM][Session:{session_id}][Worker:{worker_url}] {status} {details}")

@router.post("/")
async def chat(
    request: schemas.ChatRequest,
    db: Session = Depends(get_db)
):
    start_time = time.time()
    logger.info(f"[Chat] Request received: '{request.message[:50]}...', session_id: {request.session_id}")
    
    user = crud.get_user(db, user_id=1)
    if not user:
        user = crud.create_user(db, username="default_user")
    
    if request.session_id is None:
        session = crud.create_chat_session(db, user_id=user.id, title=request.message[:50])
        session_id_for_worker = str(session.id)
        logger.info(f"[Chat] Created new session: {session.id}")
    else:
        session = crud.get_chat_session(db, request.session_id)
        if not session:
            logger.error(f"[Chat] Session not found: {request.session_id}")
            raise HTTPException(status_code=404, detail="Session not found")
        session_id_for_worker = str(session.id)
        logger.info(f"[Chat] Using existing session: {session.id}")
    
    crud.create_message(db, session_id=session.id, role="user", content=request.message)
    
    try:
        worker_url = worker_manager.get_chat_worker()
        logger.info(f"[Chat] Selected worker: {worker_url}")
        
        async def generate_stream():
            full_response = ""
            stream_id = f"{session.id}_{int(time.time())}"
            
            try:
                request_body = {
                    "question": request.message,
                    "session_id": session_id_for_worker
                }
                
                log_stream_status(session.id, worker_url, "START", f"ID:{stream_id}")
                
                async with httpx.AsyncClient(
                    timeout=httpx.Timeout(
                        connect=15.0,
                        read=45.0,
                        write=15.0,
                        pool=10.0
                    ),
                    limits=httpx.Limits(
                        max_keepalive_connections=3,
                        max_connections=5,
                        keepalive_expiry=10.0
                    )
                ) as client:
                    
                    log_stream_status(session.id, worker_url, "CONNECTING")
                    
                    try:
                        async with client.stream(
                            "POST",
                            f"{worker_url}/chat",
                            json=request_body,
                            headers={"Content-Type": "application/json"}
                        ) as response:
                            
                            log_stream_status(session.id, worker_url, "CONNECTED", f"Status:{response.status_code}")
                            
                            if response.status_code != 200:
                                error_text = await response.aread()
                                log_stream_status(session.id, worker_url, "ERROR", f"HTTP:{response.status_code}, Body:{error_text[:200]}")
                                raise Exception(f"Worker returned status {response.status_code}")
                            
                            chunk_count = 0
                            last_chunk_time = time.time()
                            response_start_time = time.time()
                            
                            async for line in response.aiter_lines():
                                if not line.strip():
                                    continue
                                
                                chunk_count += 1
                                current_time = time.time()
                                
                                if current_time - last_chunk_time > 3.0:
                                    log_stream_status(session.id, worker_url, "SLOW_CHUNK", 
                                                    f"Chunk:{chunk_count}, Delay:{current_time - last_chunk_time:.1f}s")
                                
                                last_chunk_time = current_time
                                
                                try:
                                    data = json.loads(line)
                                    
                                    if "text" in data:
                                        chunk = data["text"]
                                        full_response += chunk
                                        yield json.dumps({
                                            "chunk": chunk,
                                            "session_id": session.id,
                                            "status": "streaming"
                                        }) + "\n"
                                        
                                        if chunk_count % 5 == 0:
                                            log_stream_status(session.id, worker_url, "PROGRESS", 
                                                            f"Chunks:{chunk_count}, TextLength:{len(full_response)}")
                                            
                                    elif "error" in data:
                                        log_stream_status(session.id, worker_url, "WORKER_ERROR", data["error"])
                                        raise Exception(f"Worker error: {data['error']}")
                                        
                                    elif data.get("status") == "completed" or data.get("is_last"):
                                        log_stream_status(session.id, worker_url, "COMPLETED_SIGNAL")
                                        break
                                        
                                except json.JSONDecodeError:
                                    log_stream_status(session.id, worker_url, "INVALID_JSON", f"Line:{line[:100]}")
                                    continue
                            
                            response_time = time.time() - response_start_time
                            log_stream_status(session.id, worker_url, "STREAM_END", 
                                            f"TotalChunks:{chunk_count}, TotalLength:{len(full_response)}, ResponseTime:{response_time:.1f}s")
                            
                    except httpx.ReadTimeout:
                        log_stream_status(session.id, worker_url, "TIMEOUT", "Read timeout from worker")
                        raise Exception("Worker timeout - no response for 45 seconds")
                    except httpx.ConnectTimeout:
                        log_stream_status(session.id, worker_url, "TIMEOUT", "Connect timeout to worker")
                        raise Exception("Cannot connect to worker")
                    except httpx.RemoteProtocolError:
                        log_stream_status(session.id, worker_url, "PROTOCOL_ERROR", "Connection closed unexpectedly")
                        raise Exception("Worker connection closed unexpectedly")
                    except httpx.StreamClosed:
                        log_stream_status(session.id, worker_url, "STREAM_CLOSED", "Stream was closed")
                
                log_stream_status(session.id, worker_url, "SAVING_TO_DB", f"Length:{len(full_response)}")
                if full_response:
                    crud.create_message(db, session_id=session.id, role="assistant", content=full_response)
                
                yield json.dumps({
                    "session_id": session.id,
                    "message": full_response,
                    "status": "completed"
                }) + "\n"
                
                total_time = time.time() - start_time
                log_stream_status(session.id, worker_url, "FINISHED", f"TotalTime:{total_time:.1f}s")
                
            except asyncio.CancelledError:
                log_stream_status(session.id, worker_url, "CANCELLED", "Client disconnected")
                raise
            except Exception as e:
                log_stream_status(session.id, worker_url, "EXCEPTION", f"Error:{str(e)}")
                error_msg = f"Error: {str(e)}"
                yield json.dumps({
                    "session_id": session.id,
                    "message": error_msg,
                    "status": "error"
                }) + "\n"
                crud.create_message(db, session_id=session.id, role="assistant", content=error_msg)
        
        return StreamingResponse(generate_stream(), media_type="application/x-ndjson")
        
    except HTTPException as e:
        logger.error(f"[Chat] HTTPException: {e.detail}")
        return {"session_id": session.id if 'session' in locals() else 0, "message": f"Error: {e.detail}", "status": "error"}
    except Exception as e:
        logger.error(f"[Chat] System error: {e}")
        return {"session_id": session.id if 'session' in locals() else 0, "message": f"System error: {str(e)}", "status": "error"}
import random
import asyncio
import time
import threading
import httpx
import json
import logging
from typing import List, Dict
from fastapi import HTTPException
from app.config import settings

logger = logging.getLogger(__name__)

class WorkerManager:
    def __init__(self):
        self.chat_worker_urls: List[str] = settings.chat_worker_urls
        self.quiz_worker_urls: List[str] = settings.quiz_worker_urls
        
        self.active_connections = {}
        self.connection_counter = 0
        self._lock = threading.Lock()
        
        logger.info(f"WorkerManager initialized:")
        logger.info(f"  Chat Workers: {len(self.chat_worker_urls)} URLs")
        for url in self.chat_worker_urls:
            logger.info(f"    - {url}")
        logger.info(f"  Quiz Workers: {len(self.quiz_worker_urls)} URLs")
        for url in self.quiz_worker_urls:
            logger.info(f"    - {url}")
    
    def get_chat_worker(self) -> str:
        if not self.chat_worker_urls:
            logger.error("No chat workers available")
            raise HTTPException(status_code=503, detail="No chat workers available. Please configure CHAT_WORKER_URLS in .env file")
        
        with self._lock:
            worker = random.choice(self.chat_worker_urls)
            conn_id = self.connection_counter
            self.connection_counter += 1
            self.active_connections[conn_id] = {
                "worker": worker,
                "start_time": time.time(),
                "status": "active",
                "type": "chat"
            }
            
            logger.info(f"[WORKER_MANAGER] Assigned worker {worker} (conn_id:{conn_id}, active:{len(self.active_connections)})")
            return worker
    
    def get_quiz_workers(self) -> List[str]:
        if not self.quiz_worker_urls:
            logger.error("Không tìm thấy QUIZ_WORKER_URLS trong cấu hình")
            raise HTTPException(status_code=503, detail="Dịch vụ Quiz chưa được cấu hình worker")
        return self.quiz_worker_urls
        
    def release_worker(self, worker_url: str, conn_id: int):
        with self._lock:
            if conn_id in self.active_connections:
                duration = time.time() - self.active_connections[conn_id]["start_time"]
                logger.info(f"[WORKER_MANAGER] Released worker {worker_url} (conn_id:{conn_id}, duration:{duration:.1f}s)")
                del self.active_connections[conn_id]
            else:
                logger.warning(f"[WORKER_MANAGER] Connection ID {conn_id} not found in active connections")
    
    def cleanup_stale_connections(self, timeout_seconds=300):
        with self._lock:
            current_time = time.time()
            stale_connections = []
            
            for conn_id, conn_info in self.active_connections.items():
                if current_time - conn_info["start_time"] > timeout_seconds:
                    stale_connections.append(conn_id)
            
            for conn_id in stale_connections:
                conn_info = self.active_connections[conn_id]
                duration = current_time - conn_info["start_time"]
                logger.warning(f"[WORKER_MANAGER] Cleaning up stale connection {conn_id} to {conn_info['worker']} (duration:{duration:.1f}s)")
                del self.active_connections[conn_id]
            
            return len(stale_connections)
    
    def get_status(self):
        with self._lock:
            current_time = time.time()
            connections_info = []
            
            for conn_id, conn_info in self.active_connections.items():
                duration = current_time - conn_info["start_time"]
                connections_info.append({
                    "conn_id": conn_id,
                    "worker": conn_info["worker"],
                    "duration_seconds": round(duration, 1),
                    "status": conn_info["status"],
                    "type": conn_info.get("type", "unknown")
                })
            
            return {
                "total_active_connections": len(self.active_connections),
                "chat_workers_count": len(self.chat_worker_urls),
                "quiz_workers_count": len(self.quiz_worker_urls),
                "connections": connections_info,
                "chat_worker_urls": self.chat_worker_urls,
                "quiz_worker_urls": self.quiz_worker_urls
            }
    
    async def call_chat_worker(self, worker_url: str, message: str) -> str:
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    f"{worker_url}/chat",
                    json={
                        "question": message,
                        "session_id": None
                    },
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                data = response.json()
                return data.get("message", "")
            except httpx.RequestError as e:
                logger.error(f"Chat worker request error ({worker_url}): {e}")
                raise HTTPException(status_code=500, detail=f"Chat worker unreachable: {str(e)}")
            except Exception as e:
                logger.error(f"Chat worker error ({worker_url}): {e}")
                raise HTTPException(status_code=500, detail=f"Chat worker error: {str(e)}")
    
    async def call_quiz_worker_stream(self, worker_url: str, topic: str, num_questions: int, topic_ids: List[int] = None):
        """Call quiz worker and stream progress updates"""
        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                response = await client.post(
                    f"{worker_url}/generate_quiz",
                    json={
                        "num_questions": num_questions,
                        "topic_ids": topic_ids or [],
                        "session_id": "proxy_stream"
                    },
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                
                # Track progress
                questions_received = 0
                
                async for line in response.aiter_lines():
                    if line.strip():
                        try:
                            data = json.loads(line)
                            
                            # Send progress update immediately
                            if data.get("status") == "processing" and "new_questions" in data:
                                questions_received += len(data["new_questions"])
                                yield {
                                    "status": "progress",
                                    "questions_received": questions_received,
                                    "total_requested": num_questions,
                                    "message": f"Đã nhận {questions_received}/{num_questions} câu hỏi"
                                }
                                
                        except json.JSONDecodeError:
                            continue
                
                # Return final result
                yield {
                    "status": "completed",
                    "questions_received": questions_received,
                    "message": "Hoàn thành nhận câu hỏi từ worker"
                }
                        
            except Exception as e:
                logger.error(f"Quiz worker stream error ({worker_url}): {e}")
                yield {
                    "status": "error",
                    "message": f"Lỗi worker: {str(e)}"
                }
worker_manager = WorkerManager()
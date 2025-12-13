import random
import asyncio
from typing import List, Dict
import httpx
import json
from fastapi import HTTPException
from app.config import settings

class WorkerManager:
    def __init__(self):
        # Đọc worker URLs từ config
        self.chat_worker_urls: List[str] = settings.chat_worker_urls
        self.quiz_worker_urls: List[str] = settings.quiz_worker_urls
        
        print(f" WorkerManager initialized:")
        print(f"   Chat Workers: {len(self.chat_worker_urls)} URLs")
        print(f"   Quiz Workers: {len(self.quiz_worker_urls)} URLs")
    
    def get_chat_worker(self) -> str:
        """Lấy ngẫu nhiên một chat worker"""
        if not self.chat_worker_urls:
            raise HTTPException(status_code=503, detail="No chat workers available. Please configure CHAT_WORKER_URLS in .env file")
        return random.choice(self.chat_worker_urls)
    
    def get_quiz_workers(self) -> List[str]:
        """Lấy tất cả quiz workers"""
        if not self.quiz_worker_urls:
            raise HTTPException(status_code=503, detail="No quiz workers available. Please configure QUIZ_WORKER_URLS in .env file")
        return self.quiz_worker_urls
    
    async def call_chat_worker(self, worker_url: str, message: str) -> str:
        """Gọi chat worker"""
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
                print(f" Chat worker request error ({worker_url}): {e}")
                raise HTTPException(status_code=500, detail=f"Chat worker unreachable: {str(e)}")
            except Exception as e:
                print(f" Chat worker error ({worker_url}): {e}")
                raise HTTPException(status_code=500, detail=f"Chat worker error: {str(e)}")
    
    async def call_quiz_worker(self, worker_url: str, topic: str, num_questions: int, topic_ids: List[int] = None) -> List[Dict]:
        """Gọi quiz worker"""
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(
                    f"{worker_url}/generate_quiz",
                    json={
                        "num_questions": num_questions,
                        "topic_ids": topic_ids or [],
                        "session_id": "proxy"
                    },
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                
                questions = []
                async for line in response.aiter_lines():
                    if line.strip():
                        try:
                            data = json.loads(line)
                            if data.get("status") == "processing" and "new_questions" in data:
                                questions.extend(data["new_questions"])
                        except json.JSONDecodeError:
                            continue
                
                return questions
            except Exception as e:
                print(f" Quiz worker error ({worker_url}): {e}")
                return []

worker_manager = WorkerManager()
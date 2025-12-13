import random
import asyncio
from typing import List, Dict
import httpx
from fastapi import HTTPException

class WorkerManager:
    def __init__(self):
        self.chat_worker_urls: List[str] = []
        self.quiz_worker_urls: List[str] = []
    
    def update_chat_workers(self, urls: List[str]):
        self.chat_worker_urls = [url.strip('/') for url in urls if url]
        print(f" Updated chat workers: {self.chat_worker_urls}")
    
    def update_quiz_workers(self, urls: List[str]):
        self.quiz_worker_urls = [url.strip('/') for url in urls if url]
        print(f" Updated quiz workers: {self.quiz_worker_urls}")
    
    def get_chat_worker(self) -> str:
        if not self.chat_worker_urls:
            raise HTTPException(status_code=503, detail="No chat workers available")
        return random.choice(self.chat_worker_urls)
    
    def get_quiz_workers(self) -> List[str]:
        if not self.quiz_worker_urls:
            raise HTTPException(status_code=503, detail="No quiz workers available")
        return self.quiz_worker_urls
    
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
                print(f" Chat worker request error ({worker_url}): {e}")
                raise HTTPException(status_code=500, detail=f"Chat worker unreachable: {str(e)}")
            except Exception as e:
                print(f" Chat worker error ({worker_url}): {e}")
                raise HTTPException(status_code=500, detail=f"Chat worker error: {str(e)}")
    
    async def call_quiz_worker(self, worker_url: str, topic: str, num_questions: int, topic_ids: List[int] = None) -> List[Dict]:
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
                print(f"Quiz worker error ({worker_url}): {e}")
                return []

worker_manager = WorkerManager()
import json
import aiofiles
from typing import Dict, List
from app.config import settings

class RAGStore:
    def __init__(self):
        self.data = []
        self.loaded = False
    
    async def load(self):
        try:
            async with aiofiles.open(settings.rag_jsonl_path, 'r', encoding='utf-8') as f:
                lines = await f.readlines()
                for line in lines:
                    if line.strip():
                        self.data.append(json.loads(line.strip()))
            self.loaded = True
            print(f" Loaded {len(self.data)} RAG entries")
        except Exception as e:
            print(f" Error loading RAG data: {e}")
    
    def get_text(self, source_id: int) -> str:
        if 0 <= source_id < len(self.data):
            return self.data[source_id].get('text', '')
        return ""
    
    def get_metadata(self, source_id: int) -> Dict:
        if 0 <= source_id < len(self.data):
            return self.data[source_id].get('metadata', {})
        return {}

rag_store = RAGStore()
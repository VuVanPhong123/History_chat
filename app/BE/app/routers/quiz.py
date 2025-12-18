from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from app.core.rag_store import rag_store
import json
import asyncio
from typing import List
from app import schemas, crud
from app.core.worker_manager import worker_manager
from app.database import get_db
from sqlalchemy.orm import Session
import httpx
import logging

# Thiết lập logging để theo dõi tiến trình tại Proxy
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(tags=["quiz"])

async def process_quiz_worker_stream(worker_url: str, num_questions: int, topic_ids: List[int], worker_id: int):
    """
    Kết nối và duy trì kết nối stream với từng Worker cụ thể.
    """
    async with httpx.AsyncClient(timeout=180.0) as client:
        try:
            async with client.stream(
                "POST",
                f"{worker_url}/generate_quiz",
                json={
                    "num_questions": num_questions,
                    "topic_ids": topic_ids or [],
                    "session_id": f"worker_{worker_id}"
                },
                headers={"Content-Type": "application/json"}
            ) as response:
                async for line in response.aiter_lines():
                    if line.strip():
                        try:
                            yield json.loads(line)
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            logger.error(f"--- [ERROR] Worker {worker_id} ({worker_url}): {str(e)}")
            yield {"status": "error", "message": str(e)}

@router.post("/generate")
async def generate_quiz(
    request: schemas.QuizRequest,
    db: Session = Depends(get_db)
):
    # Kiểm tra số lượng câu hỏi hợp lệ
    valid_counts = [10, 20, 30, 40]
    if request.num_questions not in valid_counts:
        raise HTTPException(status_code=400, detail=f"Số câu hỏi phải thuộc: {valid_counts}")
    
    workers = worker_manager.get_quiz_workers()
    if not workers:
        raise HTTPException(status_code=503, detail="Không có worker khả dụng")

    # Khởi tạo bản ghi đề thi trong DB
    topic_str = ",".join(str(tid) for tid in request.topic_ids) if request.topic_ids else "all"
    test = crud.create_quiz_test(
        db, 
        user_id=1, 
        topic=topic_str,
        total_questions=request.num_questions
    )

    async def generate_stream():
        all_questions = []
        generated_count = 0
        queue = asyncio.Queue() # Hàng đợi để gộp dữ liệu từ nhiều Worker

        # Gửi tín hiệu bắt đầu cho Frontend
        yield json.dumps({
            "test_id": test.id,
            "status": "started",
            "total_questions": request.num_questions,
            "message": "Đang kết nối với hệ thống biên soạn AI..."
        }) + "\n"

        # Phân bổ câu hỏi cho các Worker
        num_workers = len(workers)
        base = request.num_questions // num_workers
        remainder = request.num_questions % num_workers

        async def producer(url, num, w_id):
            async for update in process_quiz_worker_stream(url, num, request.topic_ids, w_id):
                await queue.put(update)

        # Kích hoạt các luồng nhận dữ liệu song song
        tasks = [
            asyncio.create_task(producer(workers[i], base + (1 if i < remainder else 0), i + 1))
            for i in range(num_workers) if (base + (1 if i < remainder else 0)) > 0
        ]

        # Vòng lặp forward dữ liệu về Frontend ngay khi nhận được
        while any(not t.done() for t in tasks) or not queue.empty():
            try:
                data = await asyncio.wait_for(queue.get(), timeout=0.1)
                
                if data.get("status") == "processing" and "new_questions" in data:
                    new_qs = data["new_questions"]
                    all_questions.extend(new_qs)
                    generated_count += len(new_qs)
                    
                    # Log tiến trình tại Server Proxy
                    logger.info(f"--- [PROXY LOG] Nhận {len(new_qs)} câu. Tiến độ: {generated_count}/{request.num_questions}")
                    
                    yield json.dumps({
                        "status": "progress",
                        "generated_count": generated_count,
                        "total_questions": request.num_questions,
                        "message": f"Đã biên soạn {generated_count}/{request.num_questions} câu hỏi..."
                    }) + "\n"
                
                elif data.get("status") == "error":
                    logger.error(f"--- [PROXY ERROR] Lỗi worker: {data.get('message')}")
            except asyncio.TimeoutError:
                continue

        # Sau khi nhận đủ, lưu vào database
        logger.info(f"--- [PROXY LOG] Hoàn tất thu thập. Đang lưu {len(all_questions)} câu vào DB.")
        saved_output = []
        for q in all_questions[:request.num_questions]:
            source_id = q.get("source_id", 0)

            # Lấy context từ RAG Store dựa trên source_id
            context_text = rag_store.get_text(int(source_id)) if source_id is not None else ""

            logger.info(f"--- [PROXY] Câu hỏi ID nguồn {source_id} -> Context: {context_text[:50]}...")

            crud.create_quiz_question(
                db, 
                test_id=test.id, 
                question_content=q["question"], 
                correct_answer=q["correct_answer"], 
                source_id=source_id
            )

            # Đóng gói kết quả gửi về FE bao gồm cả context
            saved_output.append({
                "question": q["question"],
                "options": q["options"],
                "correct_answer": q["correct_answer"],
                "explanation": q.get("explanation", ""),
                "context": context_text, 
                "source_id": source_id
            })

        # Gửi dữ liệu cuối cùng hoàn chỉnh
        yield json.dumps({
            "test_id": test.id,
            "status": "completed",
            "questions": saved_output,
            "message": "Đề thi đã được tạo thành công!"
        }) + "\n"

    return StreamingResponse(generate_stream(), media_type="application/x-ndjson")
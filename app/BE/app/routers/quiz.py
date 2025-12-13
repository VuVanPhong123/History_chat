from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
import json
import asyncio
from typing import List
from app import schemas, crud
from app.core.worker_manager import worker_manager
from app.database import get_db
from sqlalchemy.orm import Session

router = APIRouter(tags=["quiz"])

@router.post("/generate")
async def generate_quiz(
    request: schemas.QuizRequest,
    db: Session = Depends(get_db)
):
    print(f"[Quiz] Nhận request: topic={request.topic}, num_questions={request.num_questions}, topic_ids={request.topic_ids}")
    
    valid_counts = [10, 20, 30, 40]
    if request.num_questions not in valid_counts:
        raise HTTPException(status_code=400, detail=f"Number of questions must be one of: {valid_counts}")
    
    workers = worker_manager.get_quiz_workers()
    if not workers:
        raise HTTPException(status_code=503, detail="No quiz workers available")
    
    user = crud.get_user(db, user_id=1)
    if not user:
        user = crud.create_user(db, username="default_user")
    
    test = crud.create_quiz_test(
        db, 
        user_id=user.id,
        topic=request.topic,
        total_questions=request.num_questions
    )
    
    async def generate_stream():
        all_questions = []
        generated_count = 0
        
        # Gửi thông tin test ban đầu
        yield json.dumps({
            "test_id": test.id,
            "status": "started",
            "total_questions": request.num_questions,
            "generated_count": 0,
            "message": f"Bắt đầu tạo {request.num_questions} câu hỏi..."
        }) + "\n"
        
        # Phân chia công việc cho các worker
        num_workers = len(workers)
        base_per_worker = request.num_questions // num_workers
        remainder = request.num_questions % num_workers
        
        tasks = []
        for i, worker_url in enumerate(workers):
            num_for_worker = base_per_worker + (1 if i < remainder else 0)
            if num_for_worker > 0:
                task = asyncio.create_task(
                    process_quiz_worker(
                        worker_url, 
                        request.topic,
                        num_for_worker,
                        request.topic_ids,
                        i + 1,
                        len(workers)
                    )
                )
                tasks.append(task)
        
        # Thu thập kết quả từ các worker
        for task in asyncio.as_completed(tasks):
            try:
                worker_questions, worker_id, worker_total = await task
                all_questions.extend(worker_questions)
                generated_count += len(worker_questions)
                
                # Gửi tiến trình
                yield json.dumps({
                    "test_id": test.id,
                    "status": "progress",
                    "total_questions": request.num_questions,
                    "generated_count": generated_count,
                    "current_worker": worker_id,
                    "total_workers": worker_total,
                    "message": f"Worker {worker_id}/{worker_total}: Đã tạo {len(worker_questions)} câu hỏi"
                }) + "\n"
                
                # Gửi từng câu hỏi
                for q in worker_questions:
                    yield json.dumps({
                        "test_id": test.id,
                        "status": "question",
                        "question": q,
                        "message": "Nhận câu hỏi mới"
                    }) + "\n"
                    
            except Exception as e:
                print(f"Worker error: {e}")
                yield json.dumps({
                    "test_id": test.id,
                    "status": "error",
                    "message": f"Worker lỗi: {str(e)}"
                }) + "\n"
        
        # Lưu câu hỏi vào database (giới hạn số lượng)
        saved_questions = []
        for q in all_questions[:request.num_questions]:
            source_id = q.get("source_id", 0)
            
            db_question = crud.create_quiz_question(
                db,
                test_id=test.id,
                question_content=q.get("question", ""),
                correct_answer=q.get("correct_answer", ""),
                source_id=source_id
            )
            
            saved_questions.append(schemas.QuizQuestionOutput(
                question=q.get("question", ""),
                options=q.get("options", []),
                correct_answer=q.get("correct_answer", ""),
                explanation=q.get("explanation", ""),
                source_id=source_id
            ))
        
        # Gửi kết quả cuối cùng
        yield json.dumps({
            "test_id": test.id,
            "status": "completed",
            "total_questions": len(saved_questions),
            "generated_count": len(saved_questions),
            "questions": [q.dict() for q in saved_questions],
            "message": f"Hoàn thành! Đã tạo {len(saved_questions)} câu hỏi"
        }) + "\n"
    
    return StreamingResponse(generate_stream(), media_type="application/x-ndjson")

async def process_quiz_worker(worker_url: str, topic: str, num_questions: int, topic_ids: List[int], worker_id: int, total_workers: int):
    """Xử lý worker quiz và trả về câu hỏi"""
    import httpx
    
    questions = []
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            response = await client.post(
                f"{worker_url}/generate_quiz",
                json={
                    "num_questions": num_questions,
                    "topic_ids": topic_ids or [],
                    "session_id": f"worker_{worker_id}"
                },
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            
            # Đọc streaming response
            async for line in response.aiter_lines():
                if line.strip():
                    try:
                        data = json.loads(line)
                        if data.get("status") == "processing" and "new_questions" in data:
                            questions.extend(data["new_questions"])
                    except json.JSONDecodeError:
                        continue
            
            return questions, worker_id, total_workers
            
        except Exception as e:
            print(f"Quiz worker {worker_url} error: {e}")
            return [], worker_id, total_workers
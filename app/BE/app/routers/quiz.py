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
    print(f"[Quiz] Nhận request: num_questions={request.num_questions}, topic_ids={request.topic_ids}")
    
    valid_counts = [10, 20, 30, 40]
    if request.num_questions not in valid_counts:
        raise HTTPException(status_code=400, detail=f"Number of questions must be one of: {valid_counts}")
    
    # Validate topic_ids
    if request.topic_ids:
        invalid_ids = [tid for tid in request.topic_ids if tid not in range(1, 16)]
        if invalid_ids:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid topic IDs: {invalid_ids}. Valid IDs are 1-15"
            )
    
    workers = worker_manager.get_quiz_workers()
    if not workers:
        raise HTTPException(status_code=503, detail="No quiz workers available")
    
    user = crud.get_user(db, user_id=1)
    if not user:
        user = crud.create_user(db, username="default_user")
    
    # Save topic_ids as comma-separated string for database
    topic_str = ""
    if request.topic_ids:
        topic_str = ",".join(str(tid) for tid in request.topic_ids)
    else:
        topic_str = "all"  # Default value when no topic_ids specified
    
    test = crud.create_quiz_test(
        db, 
        user_id=user.id,
        topic=topic_str,  # Store topic_ids as string
        total_questions=request.num_questions
    )
    
    async def generate_stream():
        all_questions = []
        generated_count = 0
        
        # Send initial info
        yield json.dumps({
            "test_id": test.id,
            "status": "started",
            "total_questions": request.num_questions,
            "generated_count": 0,
            "topic_ids": request.topic_ids or [],  # Send topic_ids to frontend
            "message": f"Bắt đầu tạo {request.num_questions} câu hỏi..."
        }) + "\n"
        
        # Distribute work to workers
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
                        num_for_worker,
                        request.topic_ids,  # Pass topic_ids only
                        i + 1,
                        len(workers)
                    )
                )
                tasks.append(task)
        
        # Collect results from workers
        for task in asyncio.as_completed(tasks):
            try:
                worker_questions, worker_id, worker_total = await task
                all_questions.extend(worker_questions)
                generated_count += len(worker_questions)
                
                # Send progress
                yield json.dumps({
                    "test_id": test.id,
                    "status": "progress",
                    "total_questions": request.num_questions,
                    "generated_count": generated_count,
                    "current_worker": worker_id,
                    "total_workers": worker_total,
                    "topic_ids": request.topic_ids or [],  # Include topic_ids
                    "message": f"Worker {worker_id}/{worker_total}: Đã tạo {len(worker_questions)} câu hỏi"
                }) + "\n"
                
                # Send each question
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
        
        # Save questions to database (limit number)
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
        
        yield json.dumps({
            "test_id": test.id,
            "status": "completed",
            "total_questions": len(saved_questions),
            "generated_count": len(saved_questions),
            "topic_ids": request.topic_ids or [],  
            "questions": [q.dict() for q in saved_questions],
            "message": f"Hoàn thành! Đã tạo {len(saved_questions)} câu hỏi"
        }) + "\n"
    
    return StreamingResponse(generate_stream(), media_type="application/x-ndjson")

async def process_quiz_worker(worker_url: str, num_questions: int, topic_ids: List[int], worker_id: int, total_workers: int):
    """Process quiz worker and return questions"""
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
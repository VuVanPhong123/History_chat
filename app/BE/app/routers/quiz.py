from fastapi import APIRouter, Depends, HTTPException
import asyncio
from typing import List
from app import schemas, crud
from app.core.worker_manager import worker_manager
from app.core.rag_store import rag_store
from app.database import get_db
from sqlalchemy.orm import Session

router = APIRouter(tags=["quiz"])

@router.post("/generate", response_model=schemas.QuizResponse)
async def generate_quiz(
    request: schemas.QuizRequest,
    db: Session = Depends(get_db)
):
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
    
    num_workers = len(workers)
    questions_per_worker = request.num_questions // num_workers
    remainder = request.num_questions % num_workers
    
    tasks = []
    for i, worker_url in enumerate(workers):
        if i < remainder:
            num_for_worker = questions_per_worker + 1
        else:
            num_for_worker = questions_per_worker
        
        if num_for_worker > 0:
            task = worker_manager.call_quiz_worker(
                worker_url, 
                request.topic,
                num_for_worker,
                request.topic_ids
            )
            tasks.append(task)
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    all_questions = []
    for result in results:
        if isinstance(result, Exception):
            print(f"Worker error: {result}")
            continue
        all_questions.extend(result)
    
    quiz_questions = []
    for q in all_questions[:request.num_questions]:  
        source_id = q.get("source_id", 0)
        
        db_question = crud.create_quiz_question(
            db,
            test_id=test.id,
            question_content=q.get("question", ""),
            correct_answer=q.get("correct_answer", ""),
            source_id=source_id
        )
        
        # Thêm vào response
        quiz_questions.append(schemas.QuizQuestionOutput(
            question=q.get("question", ""),
            options=q.get("options", []),
            correct_answer=q.get("correct_answer", ""),
            explanation=q.get("explanation", ""),
            source_id=source_id
        ))
    
    return schemas.QuizResponse(
        test_id=test.id,
        questions=quiz_questions
    )

@router.get("/tests")
async def get_quiz_tests(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Lấy danh sách bài test"""
    user = crud.get_user(db, user_id=1)
    if not user:
        return []
    
    tests = crud.get_quiz_tests(db, user_id=user.id, skip=skip, limit=limit)
    
    return [
        {
            "id": test.id,
            "topic": test.topic,
            "score": test.score,
            "total_questions": test.total_questions,
            "created_at": test.created_at
        }
        for test in tests
    ]

@router.post("/tests/{test_id}/submit")
async def submit_quiz(
    test_id: int,
    answers: List[dict],  
    db: Session = Depends(get_db)
):
    test = db.query(crud.models.QuizTest).filter(crud.models.QuizTest.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    
    correct_count = 0
    for answer in answers:
        question_id = answer.get("question_id")
        user_answer = answer.get("answer")
        
        question = db.query(crud.models.QuizQuestion).filter(
            crud.models.QuizQuestion.id == question_id,
            crud.models.QuizQuestion.test_id == test_id
        ).first()
        
        if question:
            is_correct = (user_answer == question.correct_answer)
            question.user_answer = user_answer
            question.is_correct = is_correct
            
            if is_correct:
                correct_count += 1
    
    test.score = correct_count
    db.commit()
    
    return {
        "test_id": test_id,
        "score": correct_count,
        "total_questions": test.total_questions,
        "percentage": (correct_count / test.total_questions) * 100 if test.total_questions > 0 else 0
    }
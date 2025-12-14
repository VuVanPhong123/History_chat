from sqlalchemy.orm import Session
from app import models, schemas
from typing import List
# User operations
def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def create_user(db: Session, username: str):
    db_user = models.User(username=username)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# Chat operations
def create_chat_session(db: Session, user_id: int = 1, title: str = "New Chat"):
    db_session = models.ChatSession(user_id=user_id, title=title)
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session

def get_chat_session(db: Session, session_id: int):
    return db.query(models.ChatSession).filter(models.ChatSession.id == session_id).first()

def get_chat_sessions(db: Session, user_id: int = 1, skip: int = 0, limit: int = 100):
    return db.query(models.ChatSession).filter(
        models.ChatSession.user_id == user_id
    ).order_by(models.ChatSession.created_at.desc()).offset(skip).limit(limit).all()

def create_message(db: Session, session_id: int, role: str, content: str):
    db_message = models.Message(session_id=session_id, role=role, content=content)
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message

def get_chat_messages(db: Session, session_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.Message).filter(
        models.Message.session_id == session_id
    ).order_by(models.Message.timestamp).offset(skip).limit(limit).all()

def create_quiz_test(db: Session, user_id: int = 1, topic: str = "", total_questions: int = 0):
    db_test = models.QuizTest(user_id=user_id, topic=topic, total_questions=total_questions)
    db.add(db_test)
    db.commit()
    db.refresh(db_test)
    return db_test

def parse_topic_ids(topic_str: str) -> List[int]:
    if not topic_str or topic_str == "all":
        return []
    
    try:
        return [int(tid.strip()) for tid in topic_str.split(",") if tid.strip()]
    except ValueError:
        return []

def create_quiz_question(db: Session, test_id: int, question_content: str, correct_answer: str, source_id: int):
    db_question = models.QuizQuestion(
        test_id=test_id,
        question_content=question_content,
        correct_answer=correct_answer,
        source_id=source_id
    )
    db.add(db_question)
    db.commit()
    db.refresh(db_question)
    return db_question



def update_quiz_score(db: Session, test_id: int, score: int):
    db_test = db.query(models.QuizTest).filter(models.QuizTest.id == test_id).first()
    if db_test:
        db_test.score = score
        db.commit()
        db.refresh(db_test)
    return db_test

def get_quiz_tests(db: Session, user_id: int = 1, skip: int = 0, limit: int = 100):
    return db.query(models.QuizTest).filter(
        models.QuizTest.user_id == user_id
    ).order_by(models.QuizTest.created_at.desc()).offset(skip).limit(limit).all()
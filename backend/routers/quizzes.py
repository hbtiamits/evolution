from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
from uuid import UUID

from database import get_db
from models.course import Course
from models.quiz import Quiz
from pipeline import generate_quiz

router = APIRouter(prefix="/api/courses/{course_id}/quiz", tags=["quizzes"])


# --- Pydantic schemas ---

class QuestionPublic(BaseModel):
    """Question without the correct_index — sent to the client during the quiz."""
    id: int
    question: str
    options: List[str]


class QuizResponse(BaseModel):
    quiz_id: UUID
    course_id: UUID
    questions: List[QuestionPublic]


class AnswerSubmission(BaseModel):
    answers: List[int]  # one 0-based index per question, in order


class AnswerResult(BaseModel):
    question_id: int
    question: str
    selected_index: int
    correct_index: int
    is_correct: bool
    explanation: str


class SubmitResponse(BaseModel):
    score: int
    total: int
    percentage: float
    results: List[AnswerResult]


# --- Routes ---

def _get_course_or_404(course_id: UUID, db: Session) -> Course:
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course


@router.get("", response_model=QuizResponse)
def get_quiz(course_id: UUID, db: Session = Depends(get_db)):
    """Return existing quiz for a course (without answers)."""
    course = _get_course_or_404(course_id, db)
    quiz = db.query(Quiz).filter(Quiz.course_id == course_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not yet generated for this course")

    public_questions = [
        QuestionPublic(id=q["id"], question=q["question"], options=q["options"])
        for q in quiz.questions
    ]
    return QuizResponse(quiz_id=quiz.id, course_id=course_id, questions=public_questions)


@router.post("/generate", response_model=QuizResponse, status_code=201)
def create_quiz(course_id: UUID, db: Session = Depends(get_db)):
    """Generate (or regenerate) the quiz for a course using Claude."""
    course = _get_course_or_404(course_id, db)

    # Remove existing quiz if any
    existing = db.query(Quiz).filter(Quiz.course_id == course_id).first()
    if existing:
        db.delete(existing)
        db.flush()

    questions = generate_quiz(course)

    quiz = Quiz(course_id=course_id, questions=questions)
    db.add(quiz)
    db.commit()
    db.refresh(quiz)

    public_questions = [
        QuestionPublic(id=q["id"], question=q["question"], options=q["options"])
        for q in quiz.questions
    ]
    return QuizResponse(quiz_id=quiz.id, course_id=course_id, questions=public_questions)


@router.post("/submit", response_model=SubmitResponse)
def submit_quiz(course_id: UUID, submission: AnswerSubmission, db: Session = Depends(get_db)):
    """Grade a submitted quiz. Returns score and per-question feedback."""
    _get_course_or_404(course_id, db)
    quiz = db.query(Quiz).filter(Quiz.course_id == course_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="No quiz found for this course")

    questions = quiz.questions
    if len(submission.answers) != len(questions):
        raise HTTPException(
            status_code=422,
            detail=f"Expected {len(questions)} answers, got {len(submission.answers)}",
        )

    results = []
    score = 0
    for q, selected in zip(questions, submission.answers):
        is_correct = selected == q["correct_index"]
        if is_correct:
            score += 1
        results.append(
            AnswerResult(
                question_id=q["id"],
                question=q["question"],
                selected_index=selected,
                correct_index=q["correct_index"],
                is_correct=is_correct,
                explanation=q.get("explanation", ""),
            )
        )

    total = len(questions)
    return SubmitResponse(
        score=score,
        total=total,
        percentage=round(score / total * 100, 1),
        results=results,
    )

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from pydantic import BaseModel
from uuid import UUID
import datetime

from database import get_db
from models.course import Course
from pipeline import run_pipeline, fetch_arxiv_articles, generate_course

router = APIRouter(prefix="/api/courses", tags=["courses"])


# --- Pydantic schemas ---

class ModuleSchema(BaseModel):
    order: int
    title: str
    content: str
    key_takeaways: List[str]


class CourseListItem(BaseModel):
    id: UUID
    title: str
    domain: str
    summary: str
    source_url: Optional[str]
    created_at: datetime.datetime

    class Config:
        from_attributes = True


class CourseDetail(CourseListItem):
    modules: List[dict]
    source_title: Optional[str]


# --- Routes ---

@router.get("/", response_model=List[CourseListItem])
def list_courses(
    domain: Optional[str] = Query(None),
    limit: int = Query(20, le=100),
    offset: int = Query(0),
    db: Session = Depends(get_db),
):
    query = db.query(Course).order_by(desc(Course.created_at))
    if domain:
        query = query.filter(Course.domain == domain)
    return query.offset(offset).limit(limit).all()


@router.get("/domains", response_model=List[str])
def list_domains(db: Session = Depends(get_db)):
    rows = db.query(Course.domain).distinct().all()
    return [r[0] for r in rows]


@router.get("/{course_id}", response_model=CourseDetail)
def get_course(course_id: UUID, db: Session = Depends(get_db)):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course


@router.post("/trigger", status_code=202)
def trigger_pipeline(
    background_tasks: BackgroundTasks,
    domain: str = Query("machine_learning"),
    max_results: int = Query(3, le=10),
    db: Session = Depends(get_db),
):
    from database import SessionLocal
    background_tasks.add_task(run_pipeline, SessionLocal, domain, max_results)
    return {"message": f"Pipeline triggered for domain '{domain}'"}

from sqlalchemy import Column, String, Text, DateTime, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from database import Base


class Quiz(Base):
    __tablename__ = "quizzes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_id = Column(UUID(as_uuid=True), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, unique=True)
    questions = Column(JSON, nullable=False, default=list)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# Question JSON shape (stored inside Quiz.questions list):
# {
#   "id": 1,
#   "question": "...",
#   "options": ["A", "B", "C", "D"],
#   "correct_index": 2,       # 0-based index into options
#   "explanation": "..."
# }

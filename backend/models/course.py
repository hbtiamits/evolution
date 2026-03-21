from sqlalchemy import Column, String, Text, DateTime, JSON, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
import enum

from database import Base


class CourseStatus(str, enum.Enum):
    draft = "draft"
    published = "published"


class Course(Base):
    __tablename__ = "courses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(500), nullable=False)
    domain = Column(String(100), nullable=False)
    source_url = Column(String(1000), nullable=True)
    source_title = Column(String(500), nullable=True)
    summary = Column(Text, nullable=False)
    modules = Column(JSON, nullable=False, default=list)
    status = Column(Enum(CourseStatus), default=CourseStatus.published)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

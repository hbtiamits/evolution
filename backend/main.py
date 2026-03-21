from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from database import engine, SessionLocal
from models.course import Course
from models import *  # ensure all models are registered
from routers import courses_router
from pipeline import start_scheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup
    from database import Base
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables ready")

    # Start background scheduler
    scheduler = start_scheduler(SessionLocal)

    yield

    # Shutdown
    scheduler.shutdown()
    logger.info("Scheduler stopped")


app = FastAPI(
    title="AI Course Generator",
    description="Autonomous AI-powered course generation platform",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(courses_router)


@app.get("/health")
def health():
    return {"status": "ok"}

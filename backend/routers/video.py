import os
import uuid
import logging
from typing import Dict, Any, Optional

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel

from pipeline.video_generator import VideoGenerator

router = APIRouter(prefix="/api/video", tags=["video"])
logger = logging.getLogger(__name__)

# Simple in-memory job store (sufficient for demo)
_jobs: Dict[str, Dict[str, Any]] = {}


class GenerateRequest(BaseModel):
    prompt: str


def _run_generation(job_id: str, prompt: str):
    def cb(progress: float, message: str):
        if job_id in _jobs:
            _jobs[job_id]["progress"] = round(progress, 3)
            _jobs[job_id]["message"] = message

    gen = VideoGenerator()
    result = gen.generate(prompt, job_id, progress_cb=cb)

    if job_id in _jobs:
        _jobs[job_id]["status"] = result.get("status", "error")
        _jobs[job_id]["progress"] = 1.0
        _jobs[job_id]["result"] = result


@router.post("/generate")
def generate_video(req: GenerateRequest, background_tasks: BackgroundTasks):
    if not req.prompt.strip():
        raise HTTPException(status_code=422, detail="Prompt cannot be empty")

    job_id = uuid.uuid4().hex
    _jobs[job_id] = {
        "status": "processing",
        "progress": 0.0,
        "message": "Starting...",
        "result": None,
    }
    background_tasks.add_task(_run_generation, job_id, req.prompt.strip())
    return {"job_id": job_id, "status": "processing"}


@router.get("/jobs/{job_id}")
def get_job(job_id: str):
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    resp: Dict[str, Any] = {
        "job_id": job_id,
        "status": job["status"],
        "progress": job["progress"],
        "message": job["message"],
    }

    if job["status"] == "done" and job.get("result"):
        r = job["result"]
        resp.update(
            {
                "title": r.get("title"),
                "subtitle": r.get("subtitle"),
                "scenes": r.get("scenes"),
                "duration": r.get("duration"),
                "video_url": f"/api/video/stream/{job_id}",
            }
        )
    elif job["status"] == "error":
        resp["error"] = job.get("result", {}).get("error", "Unknown error")

    return resp


@router.get("/stream/{job_id}")
def stream_video(job_id: str):
    job = _jobs.get(job_id)
    if not job or job["status"] != "done":
        raise HTTPException(status_code=404, detail="Video not ready")

    video_path = (job.get("result") or {}).get("video_path", "")
    if not video_path or not os.path.exists(video_path):
        raise HTTPException(status_code=404, detail="Video file not found")

    return FileResponse(
        video_path,
        media_type="video/mp4",
        headers={"Content-Disposition": f'inline; filename="video_{job_id}.mp4"'},
    )


from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
from app.services.analysis_job_service import AnalysisJobService

router = APIRouter()

# Simple request model
class JobRequest(BaseModel):
    api_url: str

# Lazy load service
analysis_job_service = None

def get_job_service():
    global analysis_job_service
    if analysis_job_service is None:
        analysis_job_service = AnalysisJobService()
    return analysis_job_service

@router.post("/analysis/job")
async def submit_analysis_job(
    request: JobRequest, 
    background_tasks: BackgroundTasks
):
    """
    Submits a new analysis job.
    Accepts an API URL, fetches data, finds media, and runs analysis in background.
    """
    service = get_job_service()
    
    # Add to background queue
    background_tasks.add_task(service.process_job, request.api_url)
    
    return {
        "status": "queued", 
        "message": "Analysis job submitted successfully.",
        "target_url": request.api_url
    }

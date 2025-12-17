
from fastapi import APIRouter, UploadFile, File, Depends
from app.services.activity_service import ActivityRecognitionService
from app.services.transcription_service import TranscriptionService
import tempfile
import os
import concurrent.futures

router = APIRouter()

# Dependency Injection / Lazy Loading
activity_service = None
transcription_service = None

def get_activity_service():
    global activity_service
    if activity_service is None:
        activity_service = ActivityRecognitionService()
    return activity_service

def get_transcription_service():
    global transcription_service
    if transcription_service is None:
        transcription_service = TranscriptionService()
    return transcription_service

@router.post("/analyze-session")
async def analyze_session(
    video: UploadFile = File(...),
    activity_svc: ActivityRecognitionService = Depends(get_activity_service),
    transcription_svc: TranscriptionService = Depends(get_transcription_service)
):
    video_bytes = await video.read()
    content_type = video.content_type
    
    # We need to act as the orchestrator here (like SessionScorer used to be)
    # Ideally orchestration logic belongs in a service, not the controller/router.
    # But for now, we will orchestrate here to keep services simple.
    
    suffix = '.wav' if 'audio' in content_type else '.mp4'
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
        tmp_file.write(video_bytes)
        tmp_path = tmp_file.name

    try:
        # Audio
        audio_path = tmp_path.replace(suffix, '.wav')
        if suffix != '.wav':
             transcription_svc.extract_audio(tmp_path, audio_path)
             
        # Run in parallel
        with concurrent.futures.ThreadPoolExecutor() as executor:
            transcription_future = executor.submit(transcription_svc.transcribe_audio, audio_path)
            
            video_metrics = []
            if "video" in content_type:
                video_metrics = activity_svc.analyze_video_frames(tmp_path)
                
            transcription_result = transcription_future.result()
            
        final_result = activity_svc.calculate_final_scores(video_metrics)
        final_result["audio_transcription"] = transcription_result
        return final_result

    finally:
        try:
             os.unlink(tmp_path)
             if os.path.exists(audio_path): os.unlink(audio_path)
        except: pass

@router.get("/scoring-formula")
def get_scoring_formula(activity_svc: ActivityRecognitionService = Depends(get_activity_service)):
    return activity_svc.get_formula_info()

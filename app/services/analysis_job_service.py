
import httpx
import os
import tempfile
import concurrent.futures
from typing import Dict, Any
from app.services.activity_service import ActivityRecognitionService
from app.services.transcription_service import TranscriptionService

class AnalysisJobService:
    def __init__(self):
        self.activity_service = ActivityRecognitionService()
        self.transcription_service = TranscriptionService()

    async def process_job(self, api_url: str):
        print(f"[Job] Processing URL: {api_url}")
        
        try:
            # 1. Fetch Metadata from Next.js API
            metadata = await self._fetch_metadata(api_url)
            media_url = metadata.get("media_url") or metadata.get("s3_url") or metadata.get("url")
            
            if not media_url:
                print(f"[Job] Error: No media_url found in response from {api_url}")
                return
                
            print(f"[Job] Found Media URL: {media_url}")
            
            # 2. Download File
            file_path, content_type = await self._download_file(media_url)
            print(f"[Job] Downloaded to {file_path} ({content_type})")
            
            try:
                # 3. Analyze
                results = self._analyze_media(file_path, content_type)
                print("[Job] Analysis Complete.")
                
                # TODO: Send results back via Callback or Save to DB
                # For now, just print logic
                print(f"[Job] Result Summary - Score: {results.get('session_analysis', {}).get('overall_score')}")
                
            finally:
                # Cleanup
                if os.path.exists(file_path):
                    os.unlink(file_path)
                # Cleanup potential wav conversion
                wav_path = file_path.replace(os.path.splitext(file_path)[1], '.wav')
                if os.path.exists(wav_path):
                    try: os.unlink(wav_path)
                    except: pass
                    
        except Exception as e:
            print(f"[Job] Failed: {e}")

    async def _fetch_metadata(self, url: str) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url)
            resp.raise_for_status()
            return resp.json()

    async def _download_file(self, url: str) -> tuple[str, str]:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url)
            resp.raise_for_status()
            
            # Guess extension/type
            content_type = resp.headers.get("content-type", "")
            ext = ".mp4"
            if "audio" in content_type:
                ext = ".wav"
                
            with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
                tmp.write(resp.content)
                return tmp.name, content_type

    def _analyze_media(self, file_path: str, content_type: str) -> Dict:
        # Determine if video analysis is needed
        is_video = "video" in content_type or file_path.endswith(".mp4")
        
        # Audio extraction path
        audio_path = file_path
        if is_video:
             audio_path = file_path.rsplit('.', 1)[0] + '.wav'
             self.transcription_service.extract_audio(file_path, audio_path)
        
        # Run Analysis
        # Using ThreadPool for blocking ML operations
        with concurrent.futures.ThreadPoolExecutor() as executor:
            transcription_future = executor.submit(self.transcription_service.transcribe_audio, audio_path)
            
            video_metrics = []
            if is_video:
                print("[Job] Running Video Analysis...")
                video_metrics = self.activity_service.analyze_video_frames(file_path)
            else:
                print("[Job] Audio-only detected. Skipping Video Analysis.")
                
            transcription_result = transcription_future.result()
            
        final_result = self.activity_service.calculate_final_scores(video_metrics)
        final_result["audio_transcription"] = transcription_result
        
        return final_result

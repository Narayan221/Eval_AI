
import os
import ffmpeg
from faster_whisper import WhisperModel
from typing import Dict, List
import torch
import concurrent.futures

class TranscriptionService:
    def __init__(self, device_index=0):
        self.device_index = device_index
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        print(f"Loading TranscriptionService on {self.device}...")
        try:
             self.whisper_model = WhisperModel("large-v3", device=self.device, device_index=device_index, compute_type="int8")
        except Exception as e:
            print(f"Error loading Whisper: {e}")
            raise e

    def extract_audio(self, video_path: str, audio_path: str):
        try:
            (
                ffmpeg
                .input(video_path)
                .output(audio_path, acodec='pcm_s16le', ac=1, ar='16000')
                .overwrite_output()
                .run(quiet=True)
            )
        except Exception as e:
            print(f"Error extracting audio: {e}")
            raise e

    def transcribe_audio(self, audio_path: str) -> Dict:
        try:
            segments, info = self.whisper_model.transcribe(audio_path, beam_size=5)
            segment_list = list(segments)
            full_text = " ".join([seg.text.strip() for seg in segment_list])
            
            return {
                "text": full_text,
                "language": info.language,
                "segments": [
                    {
                        "start": seg.start,
                        "end": seg.end,
                        "text": seg.text.strip()
                    }
                    for seg in segment_list
                ]
            }
        except Exception as e:
            print(f"Transcription error: {e}")
            return {"text": "", "error": str(e)}

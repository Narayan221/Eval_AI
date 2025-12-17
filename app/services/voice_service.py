import asyncio
import io
import os
from dotenv import load_dotenv
import torch
from transformers import SpeechT5Processor, SpeechT5ForTextToSpeech, SpeechT5HifiGan
import soundfile as sf
import numpy as np
import whisper

load_dotenv()

class VoiceService:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # Load local Whisper model
        print("Loading Whisper model...")
        self.whisper_model = whisper.load_model("base", device=self.device)
        print(f"Whisper model loaded on {self.device}")
        
        # Load SpeechT5 models
        print("Loading SpeechT5 TTS models...")
        self.processor = SpeechT5Processor.from_pretrained("models/speecht5_tts")
        self.model = SpeechT5ForTextToSpeech.from_pretrained("models/speecht5_tts").to(self.device)
        self.vocoder = SpeechT5HifiGan.from_pretrained("models/speecht5_hifigan").to(self.device)
        
        # Load speaker embeddings
        from datasets import load_dataset
        embeddings_dataset = load_dataset("Matthijs/cmu-arctic-xvectors", split="validation")
        self.speaker_embeddings = torch.tensor(embeddings_dataset[7306]["xvector"]).unsqueeze(0).to(self.device)
        
        print("SpeechT5 TTS ready")
    
    async def speech_to_text(self, audio_file_path: str) -> str:
        """Convert speech to text using local Whisper"""
        def transcribe():
            result = self.whisper_model.transcribe(audio_file_path)
            return result["text"]
        
        loop = asyncio.get_event_loop()
        text = await loop.run_in_executor(None, transcribe)
        return text.strip()
    
    def clean_text_for_speech(self, text: str) -> str:
        """Clean text for natural speech synthesis"""
        import re
        
        # Remove ALL markdown and formatting
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # Remove **bold**
        text = re.sub(r'\*(.*?)\*', r'\1', text)      # Remove *italic*
        text = re.sub(r'`(.*?)`', r'\1', text)        # Remove `code`
        text = re.sub(r'#{1,6}\s*', '', text)         # Remove headers
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)  # Remove links
        
        # Remove mode indicators and brackets
        text = re.sub(r'\[.*?MODE\]\s*', '', text)    # Remove [GITTER MODE], [BARGAIN MODE]
        text = re.sub(r'\[.*?\]', '', text)           # Remove any remaining brackets
        
        # Fix common speech issues
        text = text.replace('&', 'and')
        text = text.replace('@', 'at')
        text = text.replace('#', 'number')
        text = text.replace('%', 'percent')
        text = text.replace('*', '')  # Remove any remaining asterisks
        
        # Remove extra whitespace and newlines
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    async def text_to_speech(self, text: str, output_path: str = "output.wav") -> str:
        """Convert text to speech using SpeechT5"""
        clean_text = self.clean_text_for_speech(text)
        
        def generate_speech():
            try:
                inputs = self.processor(text=clean_text, return_tensors="pt").to(self.device)
                
                with torch.no_grad():
                    speech = self.model.generate_speech(
                        inputs["input_ids"], 
                        self.speaker_embeddings, 
                        vocoder=self.vocoder
                    )
                
                # Convert to numpy and save
                speech_np = speech.cpu().numpy()
                sf.write(output_path, speech_np, samplerate=16000)
                    
            except Exception as e:
                print(f"SpeechT5 TTS generation failed: {e}")
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, generate_speech)
        
    async def text_to_speech_base64(self, text: str) -> str:
        """Convert text to speech and return base64 encoded string"""
        import base64
        
        clean_text = self.clean_text_for_speech(text)
        
        def generate_speech_b64():
            try:
                inputs = self.processor(text=clean_text, return_tensors="pt").to(self.device)
                
                with torch.no_grad():
                    speech = self.model.generate_speech(
                        inputs["input_ids"], 
                        self.speaker_embeddings, 
                        vocoder=self.vocoder
                    )
                
                # Convert to numpy
                speech_np = speech.cpu().numpy()
                
                # Save to in-memory buffer
                buffer = io.BytesIO()
                sf.write(buffer, speech_np, samplerate=16000, format='WAV')
                buffer.seek(0)
                
                # Encode to base64
                b64_audio = base64.b64encode(buffer.read()).decode("utf-8")
                return b64_audio
                    
            except Exception as e:
                print(f"SpeechT5 TTS generation failed: {e}")
                return None
        
        loop = asyncio.get_event_loop()
        b64_audio = await loop.run_in_executor(None, generate_speech_b64)
        
        return b64_audio
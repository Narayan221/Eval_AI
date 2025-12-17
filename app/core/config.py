
import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    PROJECT_NAME = "Eval AI"
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    
    # Model Paths
    YOLO_MODEL_PATH = "models/yolov8n-pose.pt"
    SPEECHT5_TTS_PATH = "models/speecht5_tts"
    SPEECHT5_VOCODER_PATH = "models/speecht5_hifigan"

    # Startup Analysis Configuration
    STARTUP_JOB_URL: str = "" # Paste your Next.js API URL here to run on startup
    JOB_INTERVAL_MINUTES: int = 5 # How often (in minutes) to re-check the URL

settings = Settings()

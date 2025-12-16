from fastapi import FastAPI, WebSocket, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import json
import asyncio
from .session_manager import AISessionManager
from .webrtc_handler import WebRTCHandler
from .analysis.video_scorer import SessionScorer
from .analysis.description_generator import DescriptionGenerator
from fastapi import UploadFile, File, Body
from pydantic import BaseModel

app = FastAPI()

# Mount static first
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/ui")
async def home(request: Request):
    print("WebRTC UI endpoint hit!")
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/")
async def root_redirect():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/ui")

@app.get("/health")
async def health():
    return {"status": "ok", "routes": [r.path for r in app.routes]}

@app.on_event("startup")
async def startup_event():
    print("Startup: Registered Routes:")
    for route in app.routes:
        print(f" - {route.path} [{route.methods if hasattr(route, 'methods') else 'WebSocket'}]")

session_manager = AISessionManager()
webrtc_handler = WebRTCHandler()
scorer = None

def get_scorer():
    global scorer
    if scorer is None:
        print("Initializing SessionScorer (GPU)...")
        scorer = SessionScorer()
        scorer = SessionScorer()
    return scorer

descriptor = None

def get_descriptor():
    global descriptor
    if descriptor is None:
        print("Initializing DescriptionGenerator (T5)...")
        descriptor = DescriptionGenerator()
    return descriptor

class DescriptionRequest(BaseModel):
    title: str

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message["type"] == "start_session":
                response = await session_manager.start_session(
                    message["title"], 
                    message["description"]
                )
                await websocket.send_text(json.dumps({
                    "type": "ai_response",
                    "content": response,
                    "speak": True
                }))
            
            elif message["type"] == "user_message":
                response = await session_manager.process_user_input(message["content"])
                await websocket.send_text(json.dumps({
                    "type": "ai_response",
                    "content": response,
                    "speak": True
                }))
            
            elif message["type"] == "voice_message":
                response = await session_manager.process_user_input(message["content"])
                await websocket.send_text(json.dumps({
                    "type": "ai_response",
                    "content": response,
                    "speak": True
                }))
            
            elif message["type"] == "webrtc_offer":
                answer = await webrtc_handler.handle_offer(message["sdp"])
                await websocket.send_text(json.dumps({
                    "type": "webrtc_answer",
                    "sdp": answer
                }))
                
    except Exception as e:
        print(f"WebSocket error: {e}")
    # Remove the finally block that was causing double close

@app.post("/analyze-session")
async def analyze_session(video: UploadFile = File(...)):
    current_scorer = get_scorer()
    video_bytes = await video.read()
    results = current_scorer.analyze_video(video_bytes, video.content_type)
    return results

@app.get("/scoring-formula")
def get_scoring_formula():
    current_scorer = get_scorer()
    return current_scorer.get_formula_info()

@app.post("/generate-description")
async def generate_description(request: DescriptionRequest):
    current_descriptor = get_descriptor()
    description = current_descriptor.generate(request.title)
    return {"description": description}


    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)

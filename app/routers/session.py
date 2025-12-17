
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.chat_service import ChatService
from app.services.webrtc_service import WebRTCService
from app.services.voice_service import VoiceService
import json

router = APIRouter()

chat_service = ChatService()
webrtc_service = WebRTCService()
# Lazy load VoiceService to potentially speed up initial import if heavy
voice_service = VoiceService()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message["type"] == "start_session":
                response_text = await chat_service.start_session(
                    message["title"], 
                    message["description"]
                )
                
                # Generate Audio
                audio_b64 = await voice_service.text_to_speech_base64(response_text)
                
                await websocket.send_text(json.dumps({
                    "type": "ai_response",
                    "content": response_text,
                    "audio": audio_b64,
                    "speak": True
                }))
            
            elif message["type"] == "user_message":
                response_text = await chat_service.process_user_input(message["content"])
                
                # Generate Audio
                audio_b64 = await voice_service.text_to_speech_base64(response_text)
                
                await websocket.send_text(json.dumps({
                    "type": "ai_response",
                    "content": response_text,
                    "audio": audio_b64,
                    "speak": True
                }))
            
            elif message["type"] == "voice_message":
                response_text = await chat_service.process_user_input(message["content"])
                
                # Generate Audio
                audio_b64 = await voice_service.text_to_speech_base64(response_text)
                
                await websocket.send_text(json.dumps({
                    "type": "ai_response",
                    "content": response_text,
                    "audio": audio_b64,
                    "speak": True
                }))
            
            elif message["type"] == "webrtc_offer":
                answer = await webrtc_service.handle_offer(message["sdp"])
                await websocket.send_text(json.dumps({
                    "type": "webrtc_answer",
                    "sdp": answer
                }))
                
    except Exception as e:
        print(f"WebSocket error: {e}")

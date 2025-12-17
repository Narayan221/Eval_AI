
from fastapi import APIRouter, Request, Depends
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/ui")
async def home(request: Request):
    print("WebRTC UI endpoint hit!")
    return templates.TemplateResponse("index.html", {"request": request})

@router.get("/")
async def root_redirect():
    return RedirectResponse(url="/ui")

@router.get("/health")
async def health():
    return {"status": "ok"}

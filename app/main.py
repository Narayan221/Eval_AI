
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
# from app.routers import ui, analysis, session
from app.routers import analysis
# from app.routers import session
# from app.routers import ui

app = FastAPI()

# Mount static files
# app.mount("/static", StaticFiles(directory="static"), name="static")

# Include Routers
# app.include_router(ui.router)
app.include_router(analysis.router)
# app.include_router(session.router)

from app.core.config import settings

@app.on_event("startup")
async def startup_event():
    print("Startup: Registered Routes:")
    for route in app.routes:
        print(f" - {route.path} [{route.methods if hasattr(route, 'methods') else 'WebSocket'}]")

    # Check for startup analysis job
    if settings.STARTUP_JOB_URL:
        print(f"[Startup] Found STARTUP_JOB_URL: {settings.STARTUP_JOB_URL}")
        print(f"[Startup] Starting Polling Loop (Interval: {settings.JOB_INTERVAL_MINUTES} mins)...")
        
        # Import here to avoid circular dependencies
        from app.services.analysis_job_service import AnalysisJobService
        import asyncio
        
        async def run_polling_loop():
            service = AnalysisJobService()
            while True:
                print("[Loop] Starting scheduled job...")
                await service.process_job(settings.STARTUP_JOB_URL)
                
                wait_seconds = settings.JOB_INTERVAL_MINUTES * 60
                print(f"[Loop] Job finished. Waiting {wait_seconds} seconds...")
                await asyncio.sleep(wait_seconds)
        
        # Run in background
        asyncio.create_task(run_polling_loop())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8081)

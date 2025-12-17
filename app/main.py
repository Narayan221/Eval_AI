
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.routers import ui, analysis, session

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include Routers
app.include_router(ui.router)
app.include_router(analysis.router)
app.include_router(session.router)

@app.on_event("startup")
async def startup_event():
    print("Startup: Registered Routes:")
    for route in app.routes:
        print(f" - {route.path} [{route.methods if hasattr(route, 'methods') else 'WebSocket'}]")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8081)

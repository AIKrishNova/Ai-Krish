from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import FileResponse

from app.api.chat import router as chat_router
from app.api.chat_stream import router as chat_stream_router

app = FastAPI(
    title="NEXUS AI",
    description="Your personal AI assistant API",
    version="0.1.0",
)

app.include_router(chat_router)
app.include_router(chat_stream_router)


@app.get("/")
async def root():
    return {
        "name": "NEXUS AI",
        "message": "Welcome to your personal AI assistant!",
        "status": "running",
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "nexus-ai-backend",
    }


@app.get("/ui", include_in_schema=False)
async def user_interface():
    """Serve the NEXUS AI web interface; existing API routes remain unchanged."""
    return FileResponse(Path(__file__).parent / "static" / "index.html")

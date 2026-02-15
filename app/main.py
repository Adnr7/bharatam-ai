"""FastAPI application entry point for Bharatam AI."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.config import settings
import os
from pathlib import Path

# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Voice-first AI assistant for discovering government welfare schemes",
    debug=settings.debug
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get the project root directory (parent of app directory)
BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"

# Mount static files - MUST be before route definitions
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
    print(f"✓ Static files mounted from: {STATIC_DIR}")
else:
    print(f"⚠ Warning: Static directory not found at {STATIC_DIR}")


@app.get("/")
async def root():
    """Root endpoint - serve the web interface."""
    index_path = STATIC_DIR / "index.html"
    
    if index_path.exists():
        return FileResponse(str(index_path))
    else:
        return {
            "name": settings.app_name,
            "version": settings.app_version,
            "status": "running",
            "message": "Web interface not found. API is available at /docs"
        }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


# Include API routers
from app.api import conversation, schemes

app.include_router(conversation.router, prefix="/conversation", tags=["conversation"])
app.include_router(schemes.router, prefix="/schemes", tags=["schemes"])

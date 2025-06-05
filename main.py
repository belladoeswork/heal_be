"""
Healura Backend - FastAPI server for real-time biometric data streaming
"""
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from api.websocket import websocket_router
from api.routes import api_router
from config.settings import settings
from utils.logger import setup_logger

logger = setup_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown"""
    logger.info("🚀 Healura Backend starting up...")
    yield
    logger.info("📴 Healura Backend shutting down...")

# Initialize FastAPI app
app = FastAPI(
    title="Healura API",
    description="Real-time biometric data processing for therapy sessions",
    version="0.1.0",
    lifespan=lifespan
)

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(websocket_router, prefix="/ws")
app.include_router(api_router, prefix="/api")

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Healura Backend is running",
        "version": "0.1.0",
        "status": "healthy"
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    from services.brainflow_service import emotibit_service
    
    return {
        "status": "healthy",
        "emotibit_connected": emotibit_service.board is not None,
        "streaming": emotibit_service.is_streaming,
        "board_info": emotibit_service.get_board_info()
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )
"""
Configuration settings for Healura backend
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings"""
    
    # Server settings
    HOST: str = "0.0.0.0"  # Railway requires 0.0.0.0
    PORT: int = int(os.environ.get("PORT", 8000))  # Railway provides PORT env var
    DEBUG: bool = os.environ.get("DEBUG", "True").lower() == "true"
    
    # EmotiBit settings
    EMOTIBIT_BOARD_ID: int = 47  # Correct EmotiBit board ID from BrainFlow
    EMOTIBIT_IP: Optional[str] = "192.168.0.255"  # Broadcast IP for EmotiBit discovery
    EMOTIBIT_PORT: int = 3131  # EmotiBit advertising port
    
    # Data processing settings
    SAMPLING_RATE: int = 25  # Hz
    BUFFER_SIZE: int = 250   # 10 seconds at 25Hz
    HRV_WINDOW_SIZE: int = 30  # seconds
    UPDATE_INTERVAL: float = 0.1  # 10Hz updates to frontend
    
    # Feature flags
    ENABLE_SYNTHETIC_DATA: bool = os.environ.get("ENABLE_SYNTHETIC_DATA", "False").lower() == "true"
    ENABLE_DATA_LOGGING: bool = True
    
    # Environment detection
    ENVIRONMENT: str = os.environ.get("ENVIRONMENT", "development")
    IS_PRODUCTION: bool = ENVIRONMENT.lower() == "production"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Global settings instance
settings = Settings()
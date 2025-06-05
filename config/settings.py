"""
Configuration settings for Healura backend
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings"""
    
    # Server settings
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    DEBUG: bool = True
    
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
    ENABLE_SYNTHETIC_DATA: bool = False  # For testing without hardware
    ENABLE_DATA_LOGGING: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Global settings instance
settings = Settings()
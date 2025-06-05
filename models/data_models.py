"""
Pydantic models for API data structures
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class DeviceStatus(BaseModel):
    """Device connection status model"""
    connected: bool = Field(description="Whether device is connected")
    streaming: bool = Field(description="Whether device is streaming data")
    board_id: Optional[int] = Field(None, description="BrainFlow board ID")
    sampling_rate: Optional[int] = Field(None, description="Sampling rate in Hz")
    device_type: str = Field(description="Type of device (e.g., EmotiBit)")

class BiometricSnapshot(BaseModel):
    """Single point-in-time biometric reading"""
    timestamp: float = Field(description="Unix timestamp")
    heart_rate: float = Field(0, description="Heart rate in BPM")
    hrv_sdnn: float = Field(0, description="HRV SDNN metric in ms")
    hrv_rmssd: float = Field(0, description="HRV RMSSD metric in ms")
    stress_score: float = Field(0, description="Stress score 0-100")
    eda_level: float = Field(0, description="Electrodermal activity level")
    temperature: float = Field(0, description="Body temperature in Celsius")
    status: str = Field(description="Processing status")

class TherapySession(BaseModel):
    """Therapy session data model"""
    session_id: str = Field(description="Unique session identifier")
    therapist_id: Optional[str] = Field(None, description="Therapist identifier")
    patient_id: Optional[str] = Field(None, description="Patient identifier")
    start_time: datetime = Field(description="Session start time")
    end_time: Optional[datetime] = Field(None, description="Session end time")
    duration_minutes: Optional[int] = Field(None, description="Session duration")
    notes: Optional[str] = Field(None, description="Session notes")

class BiometricTimeSeries(BaseModel):
    """Time series biometric data"""
    session_id: str = Field(description="Associated session ID")
    timestamps: List[float] = Field(description="Array of timestamps")
    heart_rate: List[float] = Field(description="Heart rate time series")
    hrv_metrics: List[float] = Field(description="HRV metrics time series")
    stress_scores: List[float] = Field(description="Stress score time series")
    eda_levels: List[float] = Field(description="EDA level time series")
    temperatures: List[float] = Field(description="Temperature time series")

class AlertConfig(BaseModel):
    """Configuration for real-time alerts"""
    high_stress_threshold: float = Field(80, description="Stress score threshold for alerts")
    low_hrv_threshold: float = Field(20, description="HRV threshold for alerts")
    enable_stress_alerts: bool = Field(True, description="Enable stress level alerts")
    enable_hrv_alerts: bool = Field(True, description="Enable HRV alerts")

class WebSocketMessage(BaseModel):
    """WebSocket message structure"""
    type: str = Field(description="Message type")
    timestamp: Optional[float] = Field(None, description="Message timestamp")
    data: Optional[dict] = Field(None, description="Message payload")
    error: Optional[str] = Field(None, description="Error message if applicable")
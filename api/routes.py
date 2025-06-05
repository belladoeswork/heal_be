"""
REST API routes for Healura backend
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import time

from services.brainflow_service import emotibit_service
from services.hrv_processor import hrv_processor
from models.data_models import DeviceStatus, BiometricSnapshot
from utils.logger import setup_logger

logger = setup_logger(__name__)

api_router = APIRouter()

@api_router.get("/device/status", response_model=DeviceStatus)
async def get_device_status():
    """Get current device connection and streaming status"""
    try:
        board_info = emotibit_service.get_board_info()
        return DeviceStatus(
            connected=emotibit_service.board is not None,
            streaming=emotibit_service.is_streaming,
            board_id=board_info.get('board_id'),
            sampling_rate=board_info.get('sampling_rate'),
            device_type="EmotiBit"
        )
    except Exception as e:
        logger.error(f"❌ Error getting device status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/device/connect")
async def connect_device():
    """Connect to EmotiBit device"""
    try:
        success = await emotibit_service.connect()
        if success:
            return {"message": "Device connected successfully", "success": True}
        else:
            raise HTTPException(status_code=400, detail="Failed to connect to device")
    except Exception as e:
        logger.error(f"❌ Error connecting device: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/device/disconnect")
async def disconnect_device():
    """Disconnect from EmotiBit device"""
    try:
        await emotibit_service.disconnect()
        return {"message": "Device disconnected successfully", "success": True}
    except Exception as e:
        logger.error(f"❌ Error disconnecting device: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/streaming/start")
async def start_streaming():
    """Start data streaming"""
    try:
        if not emotibit_service.board:
            raise HTTPException(status_code=400, detail="Device not connected")
        
        success = await emotibit_service.start_streaming()
        if success:
            return {"message": "Streaming started", "success": True}
        else:
            raise HTTPException(status_code=400, detail="Failed to start streaming")
    except Exception as e:
        logger.error(f"❌ Error starting streaming: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/streaming/stop")
async def stop_streaming():
    """Stop data streaming"""
    try:
        await emotibit_service.stop_streaming()
        return {"message": "Streaming stopped", "success": True}
    except Exception as e:
        logger.error(f"❌ Error stopping streaming: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/biometrics/current", response_model=BiometricSnapshot)
async def get_current_biometrics():
    """Get current biometric snapshot"""
    try:
        if not emotibit_service.is_streaming:
            raise HTTPException(status_code=400, detail="Device not streaming")
        
        # Get latest sensor data
        sensor_data = emotibit_service.get_current_data()
        if not sensor_data:
            raise HTTPException(status_code=404, detail="No data available")
        
        # Process for metrics
        processed_metrics = hrv_processor.process_realtime_data(sensor_data)
        
        return BiometricSnapshot(
            timestamp=time.time(),
            heart_rate=processed_metrics.get('heart_rate', 0),
            hrv_sdnn=processed_metrics.get('sdnn', 0),
            hrv_rmssd=processed_metrics.get('rmssd', 0),
            stress_score=processed_metrics.get('stress_score', 0),
            eda_level=processed_metrics.get('eda_level', 0),
            temperature=processed_metrics.get('temperature', 0),
            status=processed_metrics.get('status', 'unknown')
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting biometrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/biometrics/history")
async def get_biometrics_history(minutes: int = 5):
    """Get historical biometric data (placeholder for future implementation)"""
    try:
        # TODO: Implement data storage and retrieval
        # For MVP, return empty data
        return {
            "message": "Historical data not implemented in MVP",
            "timeframe_minutes": minutes,
            "data": []
        }
    except Exception as e:
        logger.error(f"❌ Error getting history: {e}")
        raise HTTPException(status_code=500, detail=str(e))
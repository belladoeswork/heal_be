"""
WebSocket endpoints for real-time data streaming
"""
import asyncio
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Any

from services.brainflow_service import emotibit_service
from services.hrv_processor import hrv_processor
from config.settings import settings
from utils.logger import setup_logger

logger = setup_logger(__name__)

websocket_router = APIRouter()

class ConnectionManager:
    """Manage WebSocket connections"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        """Accept and store WebSocket connection"""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"👋 Client {client_id} connected")
    
    def disconnect(self, client_id: str):
        """Remove WebSocket connection"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"👋 Client {client_id} disconnected")
    
    async def send_personal_message(self, message: dict, client_id: str):
        """Send message to specific client"""
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"❌ Error sending to {client_id}: {e}")
                self.disconnect(client_id)
    
    async def broadcast(self, message: dict):
        """Send message to all connected clients"""
        disconnected_clients = []
        for client_id, connection in self.active_connections.items():
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"❌ Error broadcasting to {client_id}: {e}")
                disconnected_clients.append(client_id)
        
        # Clean up disconnected clients
        for client_id in disconnected_clients:
            self.disconnect(client_id)

# Global connection manager
manager = ConnectionManager()

@websocket_router.websocket("/realtime")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time biometric data"""
    client_id = f"client_{len(manager.active_connections)}"
    await manager.connect(websocket, client_id)
    
    # Start EmotiBit connection if not already connected
    if not emotibit_service.is_streaming:
        connected = await emotibit_service.connect()
        if connected:
            await emotibit_service.start_streaming()
        else:
            await manager.send_personal_message({
                "type": "error",
                "message": "Failed to connect to EmotiBit device"
            }, client_id)
    
    try:
        # Send initial connection status
        await manager.send_personal_message({
            "type": "connection_status",
            "connected": emotibit_service.is_streaming,
            "board_info": emotibit_service.get_board_info()
        }, client_id)
        
        # Start real-time data streaming loop
        while True:
            # Get raw sensor data
            sensor_data = emotibit_service.get_current_data()
            
            if sensor_data:
                # Process data for HRV and stress metrics
                processed_metrics = hrv_processor.process_realtime_data(sensor_data)
                
                # Send data to client
                message = {
                    "type": "biometric_data",
                    "timestamp": processed_metrics.get('timestamp'),
                    "metrics": processed_metrics,
                    "raw_data": {
                        "ppg_latest": sensor_data['ppg'][-10:] if sensor_data['ppg'] else [],
                        "eda_latest": sensor_data['eda'][-10:] if sensor_data['eda'] else [],
                        "temperature": sensor_data['temperature'][-1:] if sensor_data['temperature'] else []
                    }
                }
                
                await manager.send_personal_message(message, client_id)
            else:
                # Send heartbeat when no data available
                await manager.send_personal_message({
                    "type": "heartbeat",
                    "status": "waiting_for_data"
                }, client_id)
            
            # Update at configured interval
            await asyncio.sleep(settings.UPDATE_INTERVAL)
            
    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"❌ WebSocket error for {client_id}: {e}")
        manager.disconnect(client_id)

@websocket_router.websocket("/control")
async def control_websocket(websocket: WebSocket):
    """WebSocket endpoint for device control commands"""
    client_id = f"control_{len(manager.active_connections)}"
    await manager.connect(websocket, client_id)
    
    try:
        while True:
            # Wait for control commands from client
            data = await websocket.receive_text()
            command = json.loads(data)
            
            response = await handle_control_command(command)
            await manager.send_personal_message(response, client_id)
            
    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"❌ Control WebSocket error for {client_id}: {e}")
        manager.disconnect(client_id)

async def handle_control_command(command: Dict[str, Any]) -> Dict[str, Any]:
    """Handle control commands from frontend"""
    cmd_type = command.get("type")
    
    try:
        if cmd_type == "connect":
            success = await emotibit_service.connect()
            return {
                "type": "connect_response",
                "success": success,
                "message": "Connected successfully" if success else "Connection failed"
            }
        
        elif cmd_type == "disconnect":
            await emotibit_service.disconnect()
            return {
                "type": "disconnect_response",
                "success": True,
                "message": "Disconnected successfully"
            }
        
        elif cmd_type == "start_stream":
            success = await emotibit_service.start_streaming()
            return {
                "type": "stream_response",
                "success": success,
                "streaming": emotibit_service.is_streaming
            }
        
        elif cmd_type == "stop_stream":
            await emotibit_service.stop_streaming()
            return {
                "type": "stream_response",
                "success": True,
                "streaming": emotibit_service.is_streaming
            }
        
        elif cmd_type == "get_status":
            return {
                "type": "status_response",
                "connected": emotibit_service.board is not None,
                "streaming": emotibit_service.is_streaming,
                "board_info": emotibit_service.get_board_info()
            }
        
        else:
            return {
                "type": "error",
                "message": f"Unknown command: {cmd_type}"
            }
    
    except Exception as e:
        logger.error(f"❌ Error handling command {cmd_type}: {e}")
        return {
            "type": "error",
            "message": f"Command failed: {str(e)}"
        }
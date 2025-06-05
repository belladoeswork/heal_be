"""
EmotiBit OSC service - connects to EmotiBit Oscilloscope to receive real sensor data
This is the correct approach for getting PPG, EDA, Temperature, etc.
"""
import asyncio
import socket
import time
import json
from typing import Optional, Dict, Any, List
from collections import deque
import threading
import struct

from config.settings import settings
from utils.logger import setup_logger

logger = setup_logger(__name__)

class EmotiBitOSC:
    """Connect to EmotiBit Oscilloscope via OSC/UDP to receive real sensor data"""
    
    def __init__(self):
        self.socket: Optional[socket.socket] = None
        self.connected = False
        self.streaming = False
        self.oscilloscope_ip = "127.0.0.1"  # Default to localhost
        self.osc_port = 12345  # Default OSC port
        self.data_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        
        # Real EmotiBit data streams
        self.sensor_data = {
            'ppg': deque(maxlen=250),           # Heart rate sensor data
            'eda': deque(maxlen=250),           # Electrodermal activity
            'temperature': deque(maxlen=250),   # Body temperature  
            'accelerometer': {                  # Motion data
                'x': deque(maxlen=250),
                'y': deque(maxlen=250), 
                'z': deque(maxlen=250)
            },
            'gyroscope': {                      # Rotation data
                'x': deque(maxlen=250),
                'y': deque(maxlen=250),
                'z': deque(maxlen=250)
            },
            'timestamps': deque(maxlen=250)
        }
        
        # Data quality indicators
        self.data_quality = {
            'ppg_quality': 0,
            'eda_quality': 0,
            'last_data_time': 0,
            'total_packets': 0
        }
    
    async def connect(self, oscilloscope_ip: str = "127.0.0.1", osc_port: int = 12345) -> bool:
        """Connect to EmotiBit Oscilloscope"""
        self.oscilloscope_ip = oscilloscope_ip
        self.osc_port = osc_port
        
        try:
            logger.info(f"🔗 Connecting to EmotiBit Oscilloscope at {oscilloscope_ip}:{osc_port}")
            
            # Create UDP socket for OSC communication
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # Bind to receive OSC data from Oscilloscope
            self.socket.bind(("0.0.0.0", osc_port))
            self.socket.settimeout(1.0)
            
            self.connected = True
            logger.info(f"✅ Connected to EmotiBit Oscilloscope")
            logger.info(f"📡 Listening for OSC data on port {osc_port}")
            
            # Send a test message to see if Oscilloscope is running
            await self._send_osc_message("/emotibit/ping", [])
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Connection failed: {e}")
            if self.socket:
                self.socket.close()
                self.socket = None
            return False
    
    async def _send_osc_message(self, address: str, args: List[Any]):
        """Send OSC message to Oscilloscope"""
        try:
            # Simple OSC message format
            message = self._build_osc_message(address, args)
            
            # Send to Oscilloscope
            dest_addr = (self.oscilloscope_ip, 12346)  # Send to Oscilloscope control port
            self.socket.sendto(message, dest_addr)
            
        except Exception as e:
            logger.debug(f"❌ OSC send error: {e}")
    
    def _build_osc_message(self, address: str, args: List[Any]) -> bytes:
        """Build basic OSC message"""
        # Simple OSC message format (not full OSC spec)
        message = f"{address}".encode() + b'\0'
        for arg in args:
            message += str(arg).encode() + b'\0'
        return message
    
    async def start_streaming(self) -> bool:
        """Start receiving data from EmotiBit Oscilloscope"""
        if not self.connected:
            logger.error("❌ Not connected to Oscilloscope")
            return False
        
        if self.streaming:
            logger.info("✅ Already streaming")
            return True
        
        try:
            logger.info("🔄 Starting EmotiBit data streaming from Oscilloscope...")
            
            # Send OSC commands to start streaming
            await self._send_osc_message("/emotibit/start", [])
            await self._send_osc_message("/emotibit/stream/ppg", [1])      # Enable PPG
            await self._send_osc_message("/emotibit/stream/eda", [1])      # Enable EDA
            await self._send_osc_message("/emotibit/stream/temp", [1])     # Enable Temperature
            await self._send_osc_message("/emotibit/stream/accel", [1])    # Enable Accelerometer
            await self._send_osc_message("/emotibit/stream/gyro", [1])     # Enable Gyroscope
            
            # Start data receiving thread
            self.stop_event.clear()
            self.data_thread = threading.Thread(target=self._data_receiving_loop)
            self.data_thread.daemon = True
            self.data_thread.start()
            
            self.streaming = True
            logger.info("🔄 Data streaming started")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to start streaming: {e}")
            return False
    
    def _data_receiving_loop(self):
        """Data receiving loop running in separate thread"""
        logger.info("📊 Data receiving loop started")
        
        while not self.stop_event.is_set() and self.connected:
            try:
                if not self.socket:
                    break
                
                # Receive UDP data from Oscilloscope
                try:
                    data, addr = self.socket.recvfrom(4096)
                    if data:
                        self._parse_osc_data(data)
                        self.data_quality['last_data_time'] = time.time()
                        self.data_quality['total_packets'] += 1
                        
                except socket.timeout:
                    continue  # No data available
                    
            except Exception as e:
                logger.error(f"❌ Data receiving error: {e}")
                break
        
        logger.info("📊 Data receiving loop ended")
    
    def _parse_osc_data(self, raw_data: bytes):
        """Parse OSC data from EmotiBit Oscilloscope"""
        try:
            # Convert raw OSC data to string for simple parsing
            data_str = raw_data.decode('utf-8', errors='ignore')
            
            current_time = time.time()
            
            # Look for different data types based on OSC address patterns
            if '/ppg' in data_str or '/heartrate' in data_str:
                # Extract PPG/heart rate data
                value = self._extract_numeric_value(data_str)
                if value is not None:
                    self.sensor_data['ppg'].append({'timestamp': current_time, 'value': value})
            
            elif '/eda' in data_str or '/gsr' in data_str:
                # Extract EDA/GSR data
                value = self._extract_numeric_value(data_str)
                if value is not None:
                    self.sensor_data['eda'].append({'timestamp': current_time, 'value': value})
            
            elif '/temp' in data_str or '/temperature' in data_str:
                # Extract temperature data
                value = self._extract_numeric_value(data_str)
                if value is not None:
                    self.sensor_data['temperature'].append({'timestamp': current_time, 'value': value})
            
            elif '/accel' in data_str:
                # Extract accelerometer data (x, y, z)
                values = self._extract_multiple_values(data_str, 3)
                if values and len(values) >= 3:
                    self.sensor_data['accelerometer']['x'].append({'timestamp': current_time, 'value': values[0]})
                    self.sensor_data['accelerometer']['y'].append({'timestamp': current_time, 'value': values[1]})
                    self.sensor_data['accelerometer']['z'].append({'timestamp': current_time, 'value': values[2]})
            
            elif '/gyro' in data_str:
                # Extract gyroscope data (x, y, z)
                values = self._extract_multiple_values(data_str, 3)
                if values and len(values) >= 3:
                    self.sensor_data['gyroscope']['x'].append({'timestamp': current_time, 'value': values[0]})
                    self.sensor_data['gyroscope']['y'].append({'timestamp': current_time, 'value': values[1]})
                    self.sensor_data['gyroscope']['z'].append({'timestamp': current_time, 'value': values[2]})
            
            # Always store timestamp
            self.sensor_data['timestamps'].append(current_time)
                        
        except Exception as e:
            logger.debug(f"Parse error: {e}")
    
    def _extract_numeric_value(self, data_str: str) -> Optional[float]:
        """Extract numeric value from OSC data string"""
        try:
            # Look for floating point numbers in the string
            import re
            numbers = re.findall(r'-?\d+\.?\d*', data_str)
            if numbers:
                return float(numbers[0])
        except:
            pass
        return None
    
    def _extract_multiple_values(self, data_str: str, count: int) -> Optional[List[float]]:
        """Extract multiple numeric values from OSC data string"""
        try:
            import re
            numbers = re.findall(r'-?\d+\.?\d*', data_str)
            if len(numbers) >= count:
                return [float(n) for n in numbers[:count]]
        except:
            pass
        return None
    
    def get_current_data(self) -> Optional[Dict[str, Any]]:
        """Get current sensor data"""
        if not self.streaming:
            return None
        
        try:
            # Extract recent data
            data = {
                'ppg': [d['value'] for d in list(self.sensor_data['ppg'])[-10:]],
                'eda': [d['value'] for d in list(self.sensor_data['eda'])[-10:]],
                'temperature': [d['value'] for d in list(self.sensor_data['temperature'])[-10:]],
                'accelerometer': {
                    'x': [d['value'] for d in list(self.sensor_data['accelerometer']['x'])[-10:]],
                    'y': [d['value'] for d in list(self.sensor_data['accelerometer']['y'])[-10:]],
                    'z': [d['value'] for d in list(self.sensor_data['accelerometer']['z'])[-10:]]
                },
                'gyroscope': {
                    'x': [d['value'] for d in list(self.sensor_data['gyroscope']['x'])[-10:]],
                    'y': [d['value'] for d in list(self.sensor_data['gyroscope']['y'])[-10:]],
                    'z': [d['value'] for d in list(self.sensor_data['gyroscope']['z'])[-10:]]
                },
                'timestamp': list(self.sensor_data['timestamps'])[-10:]
            }
            
            return data
            
        except Exception as e:
            logger.error(f"❌ Error getting data: {e}")
            return None
    
    async def stop_streaming(self):
        """Stop data streaming"""
        if self.streaming:
            self.streaming = False
            self.stop_event.set()
            
            if self.data_thread:
                self.data_thread.join(timeout=2)
            
            # Send stop commands
            if self.connected:
                await self._send_osc_message("/emotibit/stop", [])
            
            logger.info("⏹️ Streaming stopped")
    
    async def disconnect(self):
        """Disconnect from EmotiBit Oscilloscope"""
        await self.stop_streaming()
        
        if self.socket:
            try:
                await self._send_osc_message("/emotibit/disconnect", [])
                self.socket.close()
            except:
                pass
            self.socket = None
        
        self.connected = False
        logger.info("📴 Disconnected from EmotiBit Oscilloscope")
    
    def get_device_info(self) -> Dict[str, Any]:
        """Get device information"""
        return {
            'connected': self.connected,
            'streaming': self.streaming,
            'oscilloscope_ip': self.oscilloscope_ip,
            'osc_port': self.osc_port,
            'device_type': 'EmotiBit_via_Oscilloscope',
            'protocol': 'OSC/UDP',
            'data_quality': self.data_quality,
            'sensors': {
                'ppg_samples': len(self.sensor_data['ppg']),
                'eda_samples': len(self.sensor_data['eda']),
                'temperature_samples': len(self.sensor_data['temperature']),
                'accelerometer_samples': len(self.sensor_data['accelerometer']['x']),
                'gyroscope_samples': len(self.sensor_data['gyroscope']['x'])
            }
        }

# Global service instance
emotibit_osc = EmotiBitOSC() 
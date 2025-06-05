"""
Direct EmotiBit communication service bypassing BrainFlow
This implements the native EmotiBit protocol for real-time data streaming
"""
import asyncio
import socket
import struct
import time
import json
from typing import Optional, Dict, Any, List
from collections import deque
import threading

from config.settings import settings
from utils.logger import setup_logger

logger = setup_logger(__name__)

class EmotiBitDirect:
    """Direct EmotiBit communication using native protocol"""
    
    def __init__(self):
        self.socket: Optional[socket.socket] = None
        self.connected = False
        self.streaming = False
        self.data_buffer = deque(maxlen=1000)
        self.device_ip: Optional[str] = None
        self.data_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        
        # EmotiBit data format
        self.sensor_data = {
            'ppg': deque(maxlen=250),
            'eda': deque(maxlen=250), 
            'temperature': deque(maxlen=250),
            'accelerometer': {'x': deque(maxlen=250), 'y': deque(maxlen=250), 'z': deque(maxlen=250)},
            'gyroscope': {'x': deque(maxlen=250), 'y': deque(maxlen=250), 'z': deque(maxlen=250)},
            'timestamps': deque(maxlen=250)
        }
    
    async def discover_emotibit(self) -> Optional[str]:
        """Discover EmotiBit device on network"""
        logger.info("🔍 Discovering EmotiBit device...")
        
        try:
            # Create UDP socket for discovery
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.settimeout(5.0)
            
            # Send discovery packet
            discovery_message = b"EmotiBit_Discovery"
            broadcast_addr = ("255.255.255.255", 3131)
            
            logger.info(f"📡 Sending discovery to {broadcast_addr}")
            sock.sendto(discovery_message, broadcast_addr)
            
            # Wait for response
            try:
                data, addr = sock.recvfrom(1024)
                device_ip = addr[0]
                logger.info(f"✅ Found EmotiBit at {device_ip}")
                logger.info(f"📝 Response: {data.decode('utf-8', errors='ignore')}")
                
                sock.close()
                return device_ip
                
            except socket.timeout:
                logger.warning("⏰ No response to discovery")
                
            sock.close()
            
        except Exception as e:
            logger.error(f"❌ Discovery error: {e}")
        
        return None
    
    async def connect(self, ip_address: Optional[str] = None) -> bool:
        """Connect to EmotiBit device"""
        if self.connected:
            logger.info("✅ Already connected")
            return True
        
        # Try discovery if no IP provided
        if not ip_address:
            ip_address = await self.discover_emotibit()
            if not ip_address:
                # Try common EmotiBit IPs
                common_ips = ["192.168.0.187", "192.168.1.187", "10.0.0.187"]
                for ip in common_ips:
                    logger.info(f"🔄 Trying {ip}...")
                    if await self._try_connect(ip):
                        ip_address = ip
                        break
        
        if not ip_address:
            logger.error("❌ Could not find EmotiBit device")
            return False
        
        return await self._try_connect(ip_address)
    
    async def _try_connect(self, ip_address: str) -> bool:
        """Try to connect to specific IP"""
        try:
            logger.info(f"🔗 Connecting to EmotiBit at {ip_address}:3131")
            
            # Create TCP socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(10.0)
            
            # Connect to EmotiBit
            await asyncio.get_event_loop().run_in_executor(
                None, self.socket.connect, (ip_address, 3131)
            )
            
            self.device_ip = ip_address
            self.connected = True
            
            logger.info(f"✅ Connected to EmotiBit at {ip_address}")
            
            # Send hello message
            hello_msg = "HELLO\n"
            await self._send_command(hello_msg)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Connection failed: {e}")
            if self.socket:
                self.socket.close()
                self.socket = None
            return False
    
    async def _send_command(self, command: str) -> Optional[str]:
        """Send command to EmotiBit"""
        if not self.socket:
            return None
            
        try:
            logger.debug(f"📤 Sending: {command.strip()}")
            await asyncio.get_event_loop().run_in_executor(
                None, self.socket.send, command.encode()
            )
            
            # Try to get response (non-blocking)
            self.socket.settimeout(1.0)
            try:
                response = await asyncio.get_event_loop().run_in_executor(
                    None, self.socket.recv, 1024
                )
                response_str = response.decode('utf-8', errors='ignore').strip()
                logger.debug(f"📥 Response: {response_str}")
                return response_str
            except socket.timeout:
                return None
                
        except Exception as e:
            logger.error(f"❌ Send command error: {e}")
            return None
    
    async def start_streaming(self) -> bool:
        """Start data streaming from EmotiBit"""
        if not self.connected:
            logger.error("❌ Not connected")
            return False
        
        if self.streaming:
            logger.info("✅ Already streaming")
            return True
        
        try:
            logger.info("🔄 Starting EmotiBit data streaming...")
            
            # Send commands to start data streaming
            commands = [
                "MODE RECORDER\n",  # Set to recorder mode
                "START RECORDING\n",  # Start recording
                "DATA ON\n",  # Enable data transmission
                "PPG ON\n",  # Enable PPG
                "EDA ON\n",  # Enable EDA
                "TEMP ON\n",  # Enable temperature
                "ACCEL ON\n",  # Enable accelerometer
                "GYRO ON\n"  # Enable gyroscope
            ]
            
            for cmd in commands:
                response = await self._send_command(cmd)
                if response:
                    logger.info(f"✅ {cmd.strip()}: {response}")
                await asyncio.sleep(0.5)
            
            # Start data collection thread
            self.stop_event.clear()
            self.data_thread = threading.Thread(target=self._data_collection_loop)
            self.data_thread.daemon = True
            self.data_thread.start()
            
            self.streaming = True
            logger.info("🔄 Data streaming started")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to start streaming: {e}")
            return False
    
    def _data_collection_loop(self):
        """Data collection loop running in separate thread"""
        logger.info("📊 Data collection loop started")
        
        while not self.stop_event.is_set() and self.connected:
            try:
                if not self.socket:
                    break
                
                # Set short timeout for non-blocking read
                self.socket.settimeout(0.1)
                
                try:
                    # Read data from socket
                    data = self.socket.recv(4096)
                    if data:
                        self._parse_emotibit_data(data)
                        
                except socket.timeout:
                    continue  # No data available, continue loop
                    
            except Exception as e:
                logger.error(f"❌ Data collection error: {e}")
                break
        
        logger.info("📊 Data collection loop ended")
    
    def _parse_emotibit_data(self, raw_data: bytes):
        """Parse raw EmotiBit data packets"""
        try:
            # Convert to string and split by lines
            data_str = raw_data.decode('utf-8', errors='ignore')
            lines = data_str.strip().split('\n')
            
            for line in lines:
                if not line:
                    continue
                    
                # EmotiBit data format: timestamp,sensor_type,value
                parts = line.split(',')
                if len(parts) >= 3:
                    try:
                        timestamp = float(parts[0])
                        sensor_type = parts[1].strip()
                        value = float(parts[2])
                        
                        # Store data based on sensor type
                        current_time = time.time()
                        
                        if 'PPG' in sensor_type.upper() or 'PG' in sensor_type:
                            self.sensor_data['ppg'].append({'timestamp': current_time, 'value': value})
                        elif 'EDA' in sensor_type.upper() or 'EA' in sensor_type:
                            self.sensor_data['eda'].append({'timestamp': current_time, 'value': value})
                        elif 'TEMP' in sensor_type.upper() or 'TH' in sensor_type:
                            self.sensor_data['temperature'].append({'timestamp': current_time, 'value': value})
                        elif 'ACCEL' in sensor_type.upper() or 'AX' in sensor_type:
                            self.sensor_data['accelerometer']['x'].append({'timestamp': current_time, 'value': value})
                        elif 'ACCEL' in sensor_type.upper() or 'AY' in sensor_type:
                            self.sensor_data['accelerometer']['y'].append({'timestamp': current_time, 'value': value})
                        elif 'ACCEL' in sensor_type.upper() or 'AZ' in sensor_type:
                            self.sensor_data['accelerometer']['z'].append({'timestamp': current_time, 'value': value})
                        elif 'GYRO' in sensor_type.upper() or 'GX' in sensor_type:
                            self.sensor_data['gyroscope']['x'].append({'timestamp': current_time, 'value': value})
                        elif 'GYRO' in sensor_type.upper() or 'GY' in sensor_type:
                            self.sensor_data['gyroscope']['y'].append({'timestamp': current_time, 'value': value})
                        elif 'GYRO' in sensor_type.upper() or 'GZ' in sensor_type:
                            self.sensor_data['gyroscope']['z'].append({'timestamp': current_time, 'value': value})
                        
                        # Always store timestamp
                        self.sensor_data['timestamps'].append(current_time)
                        
                    except (ValueError, IndexError):
                        continue  # Skip malformed data
                        
        except Exception as e:
            logger.debug(f"Parse error: {e}")
    
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
                await self._send_command("STOP RECORDING\n")
                await self._send_command("DATA OFF\n")
            
            logger.info("⏹️ Streaming stopped")
    
    async def disconnect(self):
        """Disconnect from EmotiBit"""
        await self.stop_streaming()
        
        if self.socket:
            try:
                await self._send_command("GOODBYE\n")
                self.socket.close()
            except:
                pass
            self.socket = None
        
        self.connected = False
        self.device_ip = None
        logger.info("📴 Disconnected from EmotiBit")
    
    def get_device_info(self) -> Dict[str, Any]:
        """Get device information"""
        return {
            'connected': self.connected,
            'streaming': self.streaming,
            'device_ip': self.device_ip,
            'device_type': 'EmotiBit_Direct',
            'protocol': 'Native EmotiBit Protocol',
            'data_buffer_size': len(self.data_buffer),
            'sensors': {
                'ppg_samples': len(self.sensor_data['ppg']),
                'eda_samples': len(self.sensor_data['eda']),
                'temperature_samples': len(self.sensor_data['temperature']),
                'accelerometer_samples': len(self.sensor_data['accelerometer']['x']),
                'gyroscope_samples': len(self.sensor_data['gyroscope']['x'])
            }
        }

# Global service instance
emotibit_direct = EmotiBitDirect() 
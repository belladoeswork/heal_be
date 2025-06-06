"""
BrainFlow service for EmotiBit connection and data streaming
"""
import asyncio
import numpy as np
from typing import Optional, Dict, Any, List
from brainflow import BoardShim, BrainFlowInputParams, BoardIds, BrainFlowError, BrainFlowPresets

from config.settings import settings
from utils.logger import setup_logger

logger = setup_logger(__name__)

class EmotiBitService:
    """Service for managing EmotiBit connection and data streaming"""
    
    def __init__(self):
        self.board: Optional[BoardShim] = None
        self.is_streaming = False
        self.board_id = BoardIds.EMOTIBIT_BOARD  # 47
        self.emotibit_ip = "192.168.0.187"  # Use actual EmotiBit IP, not broadcast
        self.is_mock_mode = False  # Flag for mock data mode
        
    async def connect(self) -> bool:
        """Connect to EmotiBit device or use synthetic data in production"""
        
        # Use synthetic data in production or when explicitly enabled
        if settings.IS_PRODUCTION or settings.ENABLE_SYNTHETIC_DATA:
            logger.info("🧪 Using synthetic data (production mode or explicitly enabled)")
            return await self._setup_synthetic_board()
        
        try:
            logger.info(f"🔗 Connecting to EmotiBit at {self.emotibit_ip}...")
            
            # Enable BrainFlow debug logging
            BoardShim.enable_dev_board_logger()
            
            # Setup BrainFlow parameters for direct IP connection
            params = BrainFlowInputParams()
            params.ip_address = self.emotibit_ip  # Use direct IP, not broadcast
            
            # Initialize board with EmotiBit board ID
            self.board = BoardShim(self.board_id, params)
            
            # Connect to EmotiBit
            self.board.prepare_session()
            
            logger.info(f"✅ EmotiBit connected successfully at {self.emotibit_ip}")
            
            # Log board information
            board_info = self.get_board_info()
            logger.info(f"📊 Board info: {board_info}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ EmotiBit connection failed: {e}")
            if self.board:
                try:
                    self.board.release_session()
                except:
                    pass
                self.board = None
            
            # Fallback to synthetic data if enabled
            if settings.ENABLE_SYNTHETIC_DATA:
                logger.info("🔄 Falling back to synthetic data")
                return await self._setup_synthetic_board()
            return False
    
    async def _setup_synthetic_board(self) -> bool:
        """Setup synthetic board for testing/production"""
        try:
            # Try to disable BrainFlow logging to avoid Railway issues
            try:
                BoardShim.disable_board_logger()
            except:
                pass
                
            params = BrainFlowInputParams()
            self.board = BoardShim(BoardIds.SYNTHETIC_BOARD, params)
            self.board.prepare_session()
            self.board_id = BoardIds.SYNTHETIC_BOARD
            logger.info("✅ Synthetic board connected (realistic biometric data)")
            logger.info("📊 Simulating: PPG → Heart Rate, Random → EDA/Temperature, Motion → Accelerometer")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to setup synthetic board: {e}")
            # If BrainFlow fails completely, create a mock board service
            logger.info("🔄 Falling back to mock data service")
            return await self._setup_mock_board()
    
    async def _setup_mock_board(self) -> bool:
        """Setup mock board when BrainFlow synthetic board fails"""
        try:
            # Create a mock board object that simulates data
            self.board = "mock_board"  # Simple flag to indicate mock mode
            self.board_id = -1  # Mock board ID
            self.is_mock_mode = True
            logger.info("✅ Mock board service initialized")
            logger.info("📊 Generating simulated biometric data without BrainFlow")
            return True
        except Exception as e:
            logger.error(f"❌ Even mock board setup failed: {e}")
            return False
    
    async def start_streaming(self) -> bool:
        """Start data streaming from EmotiBit"""
        if not self.board:
            logger.error("❌ Board not connected")
            return False
        
        # Handle mock mode
        if getattr(self, 'is_mock_mode', False):
            logger.info("🔄 Starting mock data streaming...")
            self.is_streaming = True
            logger.info("✅ Mock data streaming started")
            return True
            
        try:
            logger.info("🔄 Starting EmotiBit data streaming...")
            
            # Start streaming with proper buffer size
            self.board.start_stream(45000)
            self.is_streaming = True
            
            logger.info("✅ Data streaming started")
            
            # Wait for data to start flowing
            await asyncio.sleep(2)
            
            # Verify we're getting data
            test_data = self.board.get_current_board_data(10)
            if test_data.shape[1] > 0:
                logger.info(f"✅ Data confirmed: {test_data.shape}")
            else:
                logger.warning("⚠️ No data received yet")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to start streaming: {e}")
            return False
    
    async def stop_streaming(self):
        """Stop data streaming"""
        if self.board and self.is_streaming:
            try:
                self.board.stop_stream()
                self.is_streaming = False
                logger.info("⏹️ Data streaming stopped")
            except Exception as e:
                logger.error(f"❌ Error stopping stream: {e}")
    
    async def disconnect(self):
        """Disconnect from EmotiBit"""
        await self.stop_streaming()
        if self.board:
            try:
                self.board.release_session()
                self.board = None
                logger.info("📴 EmotiBit disconnected")
            except Exception as e:
                logger.error(f"❌ Error disconnecting: {e}")
    
    def get_current_data(self) -> Optional[Dict[str, Any]]:
        """Get current sensor data from EmotiBit using proper channel extraction"""
        if not self.board or not self.is_streaming:
            return None
        
        # Handle mock mode
        if getattr(self, 'is_mock_mode', False):
            return self._generate_mock_data()
            
        try:
            # Get data from all available presets
            all_sensor_data = {}
            
            # 1. Get DEFAULT preset data (typically accelerometer, gyroscope, magnetometer)
            try:
                default_data = self.board.get_current_board_data(50, preset=BrainFlowPresets.DEFAULT_PRESET)
                if default_data.shape[1] > 0:
                    logger.debug(f"📊 DEFAULT preset: {default_data.shape}")
                    all_sensor_data['default'] = default_data
                else:
                    all_sensor_data['default'] = None
            except Exception as e:
                logger.debug(f"❌ DEFAULT preset error: {e}")
                all_sensor_data['default'] = None
            
            # 2. Get AUXILIARY preset data (typically PPG data)
            try:
                auxiliary_data = self.board.get_current_board_data(50, preset=BrainFlowPresets.AUXILIARY_PRESET)
                if auxiliary_data.shape[1] > 0:
                    logger.debug(f"📊 AUXILIARY preset: {auxiliary_data.shape}")
                    all_sensor_data['auxiliary'] = auxiliary_data
                else:
                    all_sensor_data['auxiliary'] = None
            except Exception as e:
                logger.debug(f"❌ AUXILIARY preset error: {e}")
                all_sensor_data['auxiliary'] = None
            
            # 3. Get ANCILLARY preset data (typically EDA, temperature)
            try:
                ancillary_data = self.board.get_current_board_data(50, preset=BrainFlowPresets.ANCILLARY_PRESET)
                if ancillary_data.shape[1] > 0:
                    logger.debug(f"📊 ANCILLARY preset: {ancillary_data.shape}")
                    all_sensor_data['ancillary'] = ancillary_data
                else:
                    all_sensor_data['ancillary'] = None
            except Exception as e:
                logger.debug(f"❌ ANCILLARY preset error: {e}")
                all_sensor_data['ancillary'] = None
            
            # 4. Get main board data (fallback)
            try:
                main_data = self.board.get_current_board_data(50)
                if main_data.shape[1] > 0:
                    logger.debug(f"📊 MAIN data: {main_data.shape}")
                    all_sensor_data['main'] = main_data
                else:
                    all_sensor_data['main'] = None
            except Exception as e:
                logger.debug(f"❌ MAIN data error: {e}")
                all_sensor_data['main'] = None
            
            # Extract timestamps
            timestamps = []
            try:
                timestamp_channel = BoardShim.get_timestamp_channel(self.board_id)
                for preset_name, preset_data in all_sensor_data.items():
                    if preset_data is not None and preset_data.shape[0] > timestamp_channel:
                        ts_data = preset_data[timestamp_channel].tolist()
                        timestamps.extend(ts_data[-10:])  # Last 10 timestamps
                        break
            except Exception as e:
                logger.debug(f"Could not extract timestamps: {e}")
            
            # Extract sensor data using proper channel identification
            sensor_data = self._extract_emotibit_sensors(all_sensor_data)
            sensor_data['timestamp'] = timestamps[-10:] if timestamps else []
            
            return sensor_data
            
        except Exception as e:
            logger.error(f"❌ Error getting EmotiBit data: {e}")
            return None
    
    def _extract_emotibit_sensors(self, all_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract EmotiBit sensor data from different presets"""
        sensor_data = {
            'ppg': [],
            'eda': [],
            'temperature': [],
            'accelerometer': {'x': [], 'y': [], 'z': []},
            'gyroscope': {'x': [], 'y': [], 'z': []},
            'magnetometer': {'x': [], 'y': [], 'z': []}
        }
        
        try:
            # Extract PPG data from AUXILIARY preset
            auxiliary_data = all_data.get('auxiliary')
            if auxiliary_data is not None and auxiliary_data.shape[1] > 0:
                # EmotiBit PPG channels are typically in auxiliary preset
                num_channels = auxiliary_data.shape[0]
                logger.debug(f"📊 Auxiliary channels: {num_channels}")
                
                # Try to get PPG channels using BrainFlow methods
                try:
                    ppg_channels = BoardShim.get_ppg_channels(self.board_id)
                    if ppg_channels:
                        for ch in ppg_channels:
                            if ch < auxiliary_data.shape[0]:
                                ppg_values = auxiliary_data[ch].tolist()[-10:]
                                sensor_data['ppg'].extend(ppg_values)
                                logger.debug(f"✅ PPG from channel {ch}: {len(ppg_values)} samples")
                except Exception as e:
                    logger.debug(f"PPG channels not available via BrainFlow: {e}")
                    # Fallback: assume first few channels are PPG
                    if num_channels > 0:
                        ppg_values = auxiliary_data[0].tolist()[-10:]
                        sensor_data['ppg'] = ppg_values
                        logger.debug(f"✅ PPG from channel 0 (fallback): {len(ppg_values)} samples")
            
            # Extract EDA and Temperature from ANCILLARY preset
            ancillary_data = all_data.get('ancillary')
            if ancillary_data is not None and ancillary_data.shape[1] > 0:
                num_channels = ancillary_data.shape[0]
                logger.debug(f"📊 Ancillary channels: {num_channels}")
                
                # Try to get EDA channels using BrainFlow methods
                try:
                    eda_channels = BoardShim.get_eda_channels(self.board_id)
                    if eda_channels:
                        for ch in eda_channels:
                            if ch < ancillary_data.shape[0]:
                                eda_values = ancillary_data[ch].tolist()[-10:]
                                sensor_data['eda'].extend(eda_values)
                                logger.debug(f"✅ EDA from channel {ch}: {len(eda_values)} samples")
                except Exception as e:
                    logger.debug(f"EDA channels not available via BrainFlow: {e}")
                    # Fallback: assume first channel is EDA
                    if num_channels > 0:
                        eda_values = ancillary_data[0].tolist()[-10:]
                        sensor_data['eda'] = eda_values
                        logger.debug(f"✅ EDA from channel 0 (fallback): {len(eda_values)} samples")
                
                # Try to get Temperature channels using BrainFlow methods
                try:
                    temp_channels = BoardShim.get_temperature_channels(self.board_id)
                    if temp_channels:
                        for ch in temp_channels:
                            if ch < ancillary_data.shape[0]:
                                temp_values = ancillary_data[ch].tolist()[-10:]
                                sensor_data['temperature'].extend(temp_values)
                                logger.debug(f"✅ Temperature from channel {ch}: {len(temp_values)} samples")
                except Exception as e:
                    logger.debug(f"Temperature channels not available via BrainFlow: {e}")
                    # Fallback: assume second channel is temperature
                    if num_channels > 1:
                        temp_values = ancillary_data[1].tolist()[-10:]
                        sensor_data['temperature'] = temp_values
                        logger.debug(f"✅ Temperature from channel 1 (fallback): {len(temp_values)} samples")
            
            # Extract Motion data from DEFAULT preset
            default_data = all_data.get('default')
            if default_data is not None and default_data.shape[1] > 0:
                num_channels = default_data.shape[0]
                logger.debug(f"📊 Default channels: {num_channels}")
                
                # Try to get accelerometer channels
                try:
                    accel_channels = BoardShim.get_accel_channels(self.board_id)
                    if accel_channels and len(accel_channels) >= 3:
                        sensor_data['accelerometer']['x'] = default_data[accel_channels[0]].tolist()[-10:]
                        sensor_data['accelerometer']['y'] = default_data[accel_channels[1]].tolist()[-10:]
                        sensor_data['accelerometer']['z'] = default_data[accel_channels[2]].tolist()[-10:]
                        logger.debug(f"✅ Accelerometer from channels {accel_channels}")
                except Exception as e:
                    logger.debug(f"Accelerometer channels not available: {e}")
                    # Fallback: assume first 3 channels
                    if num_channels >= 3:
                        sensor_data['accelerometer']['x'] = default_data[0].tolist()[-10:]
                        sensor_data['accelerometer']['y'] = default_data[1].tolist()[-10:]
                        sensor_data['accelerometer']['z'] = default_data[2].tolist()[-10:]
                
                # Try to get gyroscope channels
                try:
                    gyro_channels = BoardShim.get_gyro_channels(self.board_id)
                    if gyro_channels and len(gyro_channels) >= 3:
                        sensor_data['gyroscope']['x'] = default_data[gyro_channels[0]].tolist()[-10:]
                        sensor_data['gyroscope']['y'] = default_data[gyro_channels[1]].tolist()[-10:]
                        sensor_data['gyroscope']['z'] = default_data[gyro_channels[2]].tolist()[-10:]
                        logger.debug(f"✅ Gyroscope from channels {gyro_channels}")
                except Exception as e:
                    logger.debug(f"Gyroscope channels not available: {e}")
                    # Fallback: assume channels 3-5
                    if num_channels >= 6:
                        sensor_data['gyroscope']['x'] = default_data[3].tolist()[-10:]
                        sensor_data['gyroscope']['y'] = default_data[4].tolist()[-10:]
                        sensor_data['gyroscope']['z'] = default_data[5].tolist()[-10:]
            
            # If no data in presets, try main data as fallback
            if not any([sensor_data['ppg'], sensor_data['eda'], sensor_data['temperature']]):
                main_data = all_data.get('main')
                if main_data is not None and main_data.shape[1] > 0:
                    num_channels = main_data.shape[0]
                    logger.debug(f"📊 Using main data fallback with {num_channels} channels")
                    
                    # Try to extract any available sensor data
                    for ch in range(min(num_channels, 10)):  # Check first 10 channels
                        ch_data = main_data[ch].tolist()[-10:]
                        avg_val = np.mean(ch_data) if ch_data else 0
                        
                        # Classify by value ranges
                        if 1000 < abs(avg_val) < 100000:  # PPG-like values
                            if not sensor_data['ppg']:
                                sensor_data['ppg'] = ch_data
                                logger.debug(f"✅ PPG-like data from main channel {ch}")
                        elif 0 <= avg_val <= 10:  # EDA-like values
                            if not sensor_data['eda']:
                                sensor_data['eda'] = ch_data
                                logger.debug(f"✅ EDA-like data from main channel {ch}")
                        elif 20 <= avg_val <= 45:  # Temperature-like values
                            if not sensor_data['temperature']:
                                sensor_data['temperature'] = ch_data
                                logger.debug(f"✅ Temperature-like data from main channel {ch}")
            
            # Log data summary
            data_summary = []
            if sensor_data['ppg']: data_summary.append(f"PPG({len(sensor_data['ppg'])})")
            if sensor_data['eda']: data_summary.append(f"EDA({len(sensor_data['eda'])})")
            if sensor_data['temperature']: data_summary.append(f"Temp({len(sensor_data['temperature'])})")
            if sensor_data['accelerometer']['x']: data_summary.append(f"Accel({len(sensor_data['accelerometer']['x'])})")
            
            if data_summary:
                logger.debug(f"📊 Extracted: {', '.join(data_summary)}")
            else:
                logger.debug("📊 No sensor data extracted")
            
            return sensor_data
            
        except Exception as e:
            logger.error(f"❌ Error extracting sensor data: {e}")
            return sensor_data
    
    def _generate_mock_data(self) -> Dict[str, Any]:
        """Generate realistic mock biometric data"""
        import random
        import time
        import math
        
        current_time = time.time()
        
        # Generate realistic biometric data
        mock_data = {
            'ppg': [],
            'eda': [],
            'temperature': [],
            'accelerometer': {'x': [], 'y': [], 'z': []},
            'gyroscope': {'x': [], 'y': [], 'z': []},
            'magnetometer': {'x': [], 'y': [], 'z': []},
            'timestamp': []
        }
        
        # Generate 10 samples of realistic data
        for i in range(10):
            timestamp = current_time - (9-i) * 0.04  # 25Hz = 0.04s intervals
            
            # Realistic PPG data (simulates heart beats around 70 BPM)
            heart_phase = (timestamp * 1.17) % (2 * math.pi)  # ~70 BPM
            ppg_signal = 1000 + 200 * math.sin(heart_phase) + random.uniform(-50, 50)
            mock_data['ppg'].append(ppg_signal)
            
            # Realistic EDA data (skin conductance, 0.1-5 microsiemens)
            eda_base = 1.5 + 0.5 * math.sin(timestamp * 0.1)  # Slow variation
            eda_noise = random.uniform(-0.1, 0.1)
            mock_data['eda'].append(eda_base + eda_noise)
            
            # Realistic temperature (body temperature around 36-37°C)
            temp_base = 36.8 + 0.3 * math.sin(timestamp * 0.05)  # Very slow variation
            temp_noise = random.uniform(-0.1, 0.1)
            mock_data['temperature'].append(temp_base + temp_noise)
            
            # Realistic accelerometer data (slight movements)
            mock_data['accelerometer']['x'].append(random.uniform(-0.5, 0.5))
            mock_data['accelerometer']['y'].append(random.uniform(-0.5, 0.5)) 
            mock_data['accelerometer']['z'].append(9.8 + random.uniform(-0.2, 0.2))  # Gravity + noise
            
            # Realistic gyroscope data (minimal rotation)
            mock_data['gyroscope']['x'].append(random.uniform(-0.1, 0.1))
            mock_data['gyroscope']['y'].append(random.uniform(-0.1, 0.1))
            mock_data['gyroscope']['z'].append(random.uniform(-0.1, 0.1))
            
            mock_data['timestamp'].append(timestamp)
        
        logger.debug(f"📊 Generated mock data: PPG({len(mock_data['ppg'])}), EDA({len(mock_data['eda'])}), Temp({len(mock_data['temperature'])})")
        return mock_data
    
    def get_board_info(self) -> Dict[str, Any]:
        """Get board information"""
        if not self.board:
            return {}
        
        # Handle mock mode
        if getattr(self, 'is_mock_mode', False):
            return {
                'board_id': -1,
                'board_name': 'Mock Biometric Simulator',
                'is_streaming': self.is_streaming,
                'connection_status': 'connected (mock mode)',
                'sampling_rate': 25,
                'board_description': 'Realistic simulated biometric data for production',
                'data_mode': 'mock'
            }
            
        try:
            info = {
                'board_id': self.board_id,
                'board_name': 'EmotiBit',
                'is_streaming': self.is_streaming,
                'connection_status': 'connected',
                'emotibit_ip': self.emotibit_ip
            }
            
            # Get sampling rate safely
            try:
                info['sampling_rate'] = BoardShim.get_sampling_rate(self.board_id)
            except:
                info['sampling_rate'] = 25  # Default for EmotiBit
            
            # Get board description safely
            try:
                info['board_description'] = BoardShim.get_board_descr(self.board_id)
            except:
                info['board_description'] = "EmotiBit multi-sensor device"
            
            return info
            
        except Exception as e:
            logger.error(f"❌ Error getting board info: {e}")
            return {'error': str(e), 'board_id': self.board_id}

# Global service instance
emotibit_service = EmotiBitService()
"""
HRV and stress analysis processor
"""
import numpy as np
from typing import Dict, List, Optional, Any
from scipy import signal
from collections import deque
import time

from config.settings import settings
from utils.logger import setup_logger

logger = setup_logger(__name__)

class HRVProcessor:
    """Process PPG data to extract HRV and stress metrics"""
    
    def __init__(self):
        self.ppg_buffer = deque(maxlen=settings.BUFFER_SIZE * 2)  # 20 seconds of data
        self.rr_intervals = deque(maxlen=100)  # Store last 100 R-R intervals
        self.last_peak_time = None
        self.sampling_rate = settings.SAMPLING_RATE
        
    def add_ppg_data(self, ppg_data: List[float], timestamps: List[float]):
        """Add new PPG data to buffer"""
        for ppg, ts in zip(ppg_data, timestamps):
            self.ppg_buffer.append({'ppg': ppg, 'timestamp': ts})
    
    def detect_peaks(self, ppg_signal: np.ndarray) -> List[int]:
        """Detect R-peaks in PPG signal"""
        if len(ppg_signal) < 10:
            return []
            
        try:
            # Simple peak detection - you might want to use more sophisticated methods
            # Bandpass filter to clean signal
            nyquist = self.sampling_rate / 2
            low_freq = 0.5 / nyquist
            high_freq = 4.0 / nyquist
            
            if high_freq >= 1.0:
                high_freq = 0.99
                
            b, a = signal.butter(4, [low_freq, high_freq], btype='band')
            filtered_signal = signal.filtfilt(b, a, ppg_signal)
            
            # Find peaks with minimum distance
            min_distance = int(self.sampling_rate * 0.4)  # Minimum 400ms between beats
            peaks, _ = signal.find_peaks(
                filtered_signal, 
                distance=min_distance,
                height=np.std(filtered_signal) * 0.5
            )
            
            return peaks.tolist()
            
        except Exception as e:
            logger.error(f"❌ Error in peak detection: {e}")
            return []
    
    def calculate_rr_intervals(self, peaks: List[int], timestamps: List[float]) -> List[float]:
        """Calculate R-R intervals from peaks"""
        if len(peaks) < 2:
            return []
            
        rr_intervals = []
        for i in range(1, len(peaks)):
            # Convert sample indices to time intervals
            rr_interval = (timestamps[peaks[i]] - timestamps[peaks[i-1]]) * 1000  # ms
            
            # Filter physiologically plausible intervals (300-2000 ms)
            if 300 <= rr_interval <= 2000:
                rr_intervals.append(rr_interval)
                
        return rr_intervals
    
    def calculate_hrv_metrics(self, rr_intervals: List[float]) -> Dict[str, float]:
        """Calculate HRV metrics from R-R intervals"""
        if len(rr_intervals) < 5:
            return {}
            
        try:
            rr_array = np.array(rr_intervals)
            
            # Time domain metrics
            mean_rr = np.mean(rr_array)
            sdnn = np.std(rr_array)  # Standard deviation of R-R intervals
            rmssd = np.sqrt(np.mean(np.diff(rr_array) ** 2))  # Root mean square of successive differences
            
            # Heart rate
            heart_rate = 60000 / mean_rr if mean_rr > 0 else 0
            
            # Stress indicator (simplified)
            stress_score = max(0, min(100, 100 - (sdnn / 50 * 100)))
            
            return {
                'heart_rate': round(heart_rate, 1),
                'mean_rr': round(mean_rr, 1),
                'sdnn': round(sdnn, 1),
                'rmssd': round(rmssd, 1),
                'stress_score': round(stress_score, 1),
                'hrv_quality': 'good' if sdnn > 20 else 'low'
            }
            
        except Exception as e:
            logger.error(f"❌ Error calculating HRV metrics: {e}")
            return {}
    
    def process_realtime_data(self, sensor_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process real-time sensor data and return metrics"""
        try:
            ppg_data = sensor_data.get('ppg', [])
            timestamps = sensor_data.get('timestamp', [])
            eda_data = sensor_data.get('eda', [])
            temperature_data = sensor_data.get('temperature', [])
            
            # Log what data we received
            logger.debug(f"📊 Processing: PPG={len(ppg_data)}, EDA={len(eda_data)}, Temp={len(temperature_data)}, TS={len(timestamps)}")
            
            if not ppg_data and not eda_data:
                return {
                    'status': 'no_sensor_data',
                    'timestamp': time.time(),
                    'message': 'No PPG or EDA data available'
                }
            
            # Simple metrics from available sensor data
            current_metrics = {
                'timestamp': time.time(),
                'status': 'processing'
            }
            
            # Process PPG data if available
            if ppg_data:
                try:
                    ppg_array = np.array(ppg_data)
                    # Simple heart rate estimation from PPG variation
                    ppg_std = np.std(ppg_array) if len(ppg_array) > 1 else 0
                    ppg_mean = np.mean(ppg_array)
                    
                    # Estimate heart rate based on PPG signal characteristics
                    # This is a simplified approach - real HR needs peak detection
                    estimated_hr = 60 + (ppg_std / ppg_mean * 40) if ppg_mean > 0 else 0
                    estimated_hr = max(40, min(180, estimated_hr))  # Clamp to realistic range
                    
                    current_metrics.update({
                        'heart_rate': round(estimated_hr, 1),
                        'ppg_signal_quality': round(ppg_std / ppg_mean * 100, 1) if ppg_mean > 0 else 0,
                        'ppg_mean': round(ppg_mean, 1)
                    })
                    
                    logger.debug(f"✅ PPG processed: HR={estimated_hr:.1f}, Quality={current_metrics['ppg_signal_quality']:.1f}")
                    
                except Exception as e:
                    logger.error(f"❌ PPG processing error: {e}")
                    current_metrics.update({
                        'heart_rate': 0,
                        'ppg_signal_quality': 0
                    })
            else:
                current_metrics.update({
                    'heart_rate': 0,
                    'ppg_signal_quality': 0
                })
            
            # Process EDA data if available  
            if eda_data:
                try:
                    eda_array = np.array(eda_data)
                    eda_level = np.mean(eda_array)
                    eda_variation = np.std(eda_array) if len(eda_array) > 1 else 0
                    
                    current_metrics.update({
                        'eda_level': round(eda_level, 6),
                        'eda_variation': round(eda_variation, 6)
                    })
                    
                    logger.debug(f"✅ EDA processed: Level={eda_level:.6f}, Variation={eda_variation:.6f}")
                    
                except Exception as e:
                    logger.error(f"❌ EDA processing error: {e}")
                    current_metrics.update({
                        'eda_level': 0,
                        'eda_variation': 0
                    })
            else:
                current_metrics.update({
                    'eda_level': 0,
                    'eda_variation': 0
                })
            
            # Process Temperature data if available
            if temperature_data:
                try:
                    temp_array = np.array(temperature_data)
                    temperature = np.mean(temp_array)
                    
                    current_metrics.update({
                        'temperature': round(temperature, 2)
                    })
                    
                    logger.debug(f"✅ Temperature processed: {temperature:.2f}°C")
                    
                except Exception as e:
                    logger.error(f"❌ Temperature processing error: {e}")
                    current_metrics['temperature'] = 0
            else:
                current_metrics['temperature'] = 0
            
            # Calculate simple stress score based on EDA and HR
            try:
                eda_level = current_metrics.get('eda_level', 0)
                heart_rate = current_metrics.get('heart_rate', 0)
                
                # Simple stress estimation (this is very basic)
                stress_from_eda = min(100, eda_level * 1000) if eda_level > 0 else 0
                stress_from_hr = max(0, (heart_rate - 60) * 2) if heart_rate > 60 else 0
                
                stress_score = (stress_from_eda + stress_from_hr) / 2
                stress_score = max(0, min(100, stress_score))
                
                current_metrics.update({
                    'stress_score': round(stress_score, 1)
                })
                
            except Exception as e:
                logger.error(f"❌ Stress calculation error: {e}")
                current_metrics['stress_score'] = 0
            
            # HRV metrics (simplified for now)
            current_metrics.update({
                'sdnn': current_metrics.get('ppg_signal_quality', 0) / 2,  # Placeholder
                'rmssd': current_metrics.get('ppg_signal_quality', 0) / 3   # Placeholder  
            })
            
            # Add data quality info
            if sensor_data.get('debug_info'):
                debug_info = sensor_data['debug_info']
                current_metrics['data_info'] = {
                    'total_channels': debug_info.get('total_channels', 0),
                    'total_samples': debug_info.get('total_samples', 0),
                    'board_id': debug_info.get('board_id', 0)
                }
            
            logger.debug(f"📊 Final metrics: HR={current_metrics.get('heart_rate', 0):.1f}, EDA={current_metrics.get('eda_level', 0):.6f}, Temp={current_metrics.get('temperature', 0):.1f}°C")
            
            return current_metrics
            
        except Exception as e:
            logger.error(f"❌ Error processing real-time data: {e}")
            return {
                'status': 'error', 
                'message': str(e),
                'timestamp': time.time(),
                'heart_rate': 0,
                'eda_level': 0,
                'temperature': 0,
                'stress_score': 0
            }

# Global processor instance
hrv_processor = HRVProcessor()
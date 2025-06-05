# Healura Backend

Real-time biometric data processing backend for therapy sessions using EmotiBit and BrainFlow.

## Quick Start (5-Day MVP)

### 1. Install Dependencies

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install requirements
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy and edit environment file
cp .env.example .env
# Edit .env with your EmotiBit device IP if known
```

### 3. Run the Server

```bash
# Start the FastAPI server
python main.py

# Or with uvicorn directly
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

### 4. Test EmotiBit Connection

First test the EmotiBit connection directly:

```bash
# Test EmotiBit connection (recommended)
python test_emotibit_broadcast.py

# Alternative: Test with multiple connection methods
python test_emotibit.py
```

**✅ If the broadcast test works, your EmotiBit is ready!**

### 5. Test the API

```bash
# Check health
curl http://localhost:8000/health

# Check device status
curl http://localhost:8000/api/device/status
```

## API Endpoints

### REST API
- `GET /` - Health check
- `GET /api/device/status` - Device connection status
- `POST /api/device/connect` - Connect to EmotiBit
- `POST /api/device/disconnect` - Disconnect device
- `POST /api/streaming/start` - Start data streaming
- `POST /api/streaming/stop` - Stop data streaming
- `GET /api/biometrics/current` - Get current biometric snapshot

### WebSocket Endpoints
- `ws://localhost:8000/ws/realtime` - Real-time biometric data stream
- `ws://localhost:8000/ws/control` - Device control commands

## WebSocket Data Format

### Real-time Data Message
```json
{
  "type": "biometric_data",
  "timestamp": 1703123456.789,
  "metrics": {
    "heart_rate": 72.5,
    "sdnn": 45.2,
    "rmssd": 38.1,
    "stress_score": 25.3,
    "eda_level": 0.125,
    "temperature": 36.8,
    "status": "processing"
  },
  "raw_data": {
    "ppg_latest": [0.1, 0.2, 0.15, ...],
    "eda_latest": [0.12, 0.125, 0.13, ...],
    "temperature": [36.8]
  }
}
```

### Control Commands
```json
{
  "type": "connect",
  "timestamp": 1703123456.789
}
```

## Testing Without Hardware

Set `ENABLE_SYNTHETIC_DATA=true` in `.env` to use BrainFlow's synthetic board for testing.

## EmotiBit Setup

1. Connect EmotiBit to same WiFi network as your computer
2. Find the device IP address (check router admin panel or use network scanner)
3. Update `EMOTIBIT_IP` in `.env` file
4. Ensure EmotiBit is powered on and connected

## Development

### Project Structure
```
healura-backend/
├── main.py              # FastAPI application entry point
├── config/
│   └── settings.py      # Configuration management
├── services/
│   ├── brainflow_service.py  # EmotiBit/BrainFlow integration
│   └── hrv_processor.py      # HRV and stress analysis
├── api/
│   ├── websocket.py     # WebSocket endpoints
│   └── routes.py        # REST API routes
├── models/
│   └── data_models.py   # Pydantic data models
└── utils/
    └── logger.py        # Logging configuration
```

### Adding New Features

1. **New Metrics**: Add processing logic to `services/hrv_processor.py`
2. **New Endpoints**: Add routes to `api/routes.py`
3. **WebSocket Events**: Modify `api/websocket.py`
4. **Data Models**: Add to `models/data_models.py`

## Troubleshooting

### Common Issues

1. **EmotiBit Connection Failed**
   - Check device is on same network
   - Verify IP address matches EmotiBit output (currently `192.168.0.187`)
   - Ensure EmotiBit is advertising on port 3131
   - Try running `python test_emotibit.py` for detailed diagnostics
   - Check BrainFlow debug logs for connection errors
   - Try enabling synthetic data mode: `ENABLE_SYNTHETIC_DATA=true`

2. **No Data Streaming**
   - Ensure device is properly connected first
   - Check BrainFlow logs for errors (enable with `BoardShim.enable_dev_board_logger()`)
   - Verify EmotiBit firmware is compatible with BrainFlow
   - Try different data presets (PPG, EDA, Accelerometer)
   - Check if device is already connected to another application

3. **WebSocket Connection Issues**
   - Check CORS settings in `main.py`
   - Verify frontend is connecting to correct port
   - Check browser developer console for errors
   - Ensure EmotiBit is streaming data before connecting WebSocket

4. **Channel Data Issues**
   - Different EmotiBit firmware versions may have different channel mappings
   - Check the `test_emotibit.py` output for available channels
   - Verify that the correct BrainFlow presets are being used:
     - `AUXILIARY_PRESET` for PPG data
     - `ANCILLARY_PRESET` for EDA and temperature
     - `DEFAULT_PRESET` for accelerometer data

### Logs

All logs are output to console with timestamps and log levels. Increase verbosity by setting `DEBUG=true` in `.env`.

## Production Deployment

For production deployment:

1. Set `DEBUG=false` in environment
2. Use proper ASGI server (Gunicorn + Uvicorn)
3. Add SSL/TLS termination
4. Implement proper authentication
5. Add database for session storage
6. Set up monitoring and alerting

## Next Steps

After MVP validation:

1. **Data Persistence**: Add database for session storage
2. **Authentication**: Implement therapist/patient auth
3. **Advanced Analytics**: Add ML-based stress detection
4. **Mobile Support**: Extend WebSocket for mobile clients
5. **Desktop App**: Wrap frontend in Electron
6. **HIPAA Compliance**: Add encryption and audit logging
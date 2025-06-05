#!/usr/bin/env python3
"""
Test WebSocket connection for real-time data streaming
"""
import asyncio
import websockets
import json

async def test_websocket():
    """Connect to WebSocket and display real-time data"""
    uri = "ws://localhost:8000/ws/realtime"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("🔗 Connected to WebSocket!")
            print("📊 Waiting for real-time data...")
            print("=" * 50)
            
            # Listen for messages for 30 seconds
            timeout = 30
            start_time = asyncio.get_event_loop().time()
            
            while asyncio.get_event_loop().time() - start_time < timeout:
                try:
                    # Wait for message with timeout
                    message = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                    data = json.loads(message)
                    
                    print(f"📨 Message type: {data.get('type')}")
                    
                    if data.get('type') == 'biometric_data':
                        metrics = data.get('metrics', {})
                        print(f"❤️  Heart Rate: {metrics.get('heart_rate', 0)} BPM")
                        print(f"📈 HRV SDNN: {metrics.get('sdnn', 0)} ms")
                        print(f"😰 Stress Score: {metrics.get('stress_score', 0)}")
                        print(f"🌡️  Temperature: {metrics.get('temperature', 0)}°C")
                        print(f"⚡ EDA Level: {metrics.get('eda_level', 0)}")
                        print(f"✅ Status: {metrics.get('status', 'unknown')}")
                        
                        # Show some raw data
                        raw_data = data.get('raw_data', {})
                        ppg_data = raw_data.get('ppg_latest', [])
                        if ppg_data:
                            print(f"📊 Latest PPG: {ppg_data[-3:]}...")  # Last 3 values
                        
                    elif data.get('type') == 'connection_status':
                        print(f"🔗 Connection Status: {data}")
                    
                    elif data.get('type') == 'heartbeat':
                        print(f"💓 Heartbeat: {data.get('status')}")
                    
                    elif data.get('type') == 'error':
                        print(f"❌ Error: {data.get('message')}")
                    
                    print("-" * 30)
                    
                except asyncio.TimeoutError:
                    print("⏰ No message received in 2 seconds...")
                    continue
                
    except Exception as e:
        print(f"❌ WebSocket error: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket()) 
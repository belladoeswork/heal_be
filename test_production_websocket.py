#!/usr/bin/env python3
"""
Test production WebSocket connection
"""
import asyncio
import websockets
import json

async def test_production_websocket():
    """Test WebSocket connection to production Railway deployment"""
    
    # Your Railway WebSocket URL
    uri = "wss://healbe-production.up.railway.app/ws/realtime"
    
    print(f"🔗 Connecting to production WebSocket: {uri}")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to production WebSocket!")
            print("📊 Waiting for real-time data...")
            print("=" * 50)
            
            # Listen for messages for 30 seconds
            timeout = 30
            start_time = asyncio.get_event_loop().time()
            
            while asyncio.get_event_loop().time() - start_time < timeout:
                try:
                    # Wait for message with timeout
                    message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(message)
                    
                    print(f"📨 Message type: {data.get('type')}")
                    
                    if data.get('type') == 'biometric_data':
                        metrics = data.get('metrics', {})
                        print(f"❤️  Heart Rate: {metrics.get('heart_rate', 0)} BPM")
                        print(f"😰 Stress Score: {metrics.get('stress_score', 0)}")
                        print(f"🌡️  Temperature: {metrics.get('temperature', 0)}°C")
                        print(f"⚡ EDA Level: {metrics.get('eda_level', 0)}")
                        print(f"✅ Status: {metrics.get('status', 'unknown')}")
                        
                    elif data.get('type') == 'connection_status':
                        print(f"🔗 Connection Status: {data}")
                    
                    elif data.get('type') == 'heartbeat':
                        print(f"💓 Heartbeat: {data.get('status')}")
                    
                    elif data.get('type') == 'error':
                        print(f"❌ Error: {data.get('message')}")
                    
                    print("-" * 30)
                    
                except asyncio.TimeoutError:
                    print("⏰ No message received in 5 seconds...")
                    continue
                
    except Exception as e:
        print(f"❌ WebSocket error: {e}")
        print("💡 Check:")
        print("   - Railway deployment is running")
        print("   - WebSocket endpoint is accessible")
        print("   - CORS settings allow your domain")

if __name__ == "__main__":
    asyncio.run(test_production_websocket()) 
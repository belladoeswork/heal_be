#!/usr/bin/env python3
import asyncio
import websockets
import json

async def quick_test():
    uri = 'wss://healbe-production.up.railway.app/ws/realtime'
    try:
        async with websockets.connect(uri) as ws:
            print('✅ Connected!')
            for i in range(5):
                msg = await asyncio.wait_for(ws.recv(), timeout=3.0)
                data = json.loads(msg)
                print(f'{i+1}: {data.get("type")} - {data.get("message", "")}')
                if data.get('type') == 'biometric_data':
                    metrics = data.get('metrics', {})
                    print(f'   ❤️ HR: {metrics.get("heart_rate", 0)} BPM')
                    print(f'   🌡️ Temp: {metrics.get("temperature", 0)}°C')
                    print(f'   ⚡ EDA: {metrics.get("eda_level", 0)}')
                    break
    except Exception as e:
        print(f'❌ Error: {e}')

if __name__ == "__main__":
    asyncio.run(quick_test()) 
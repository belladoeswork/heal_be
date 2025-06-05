#!/usr/bin/env python3
"""
Debug script to see raw EmotiBit data
"""
import requests
import time
import json

def test_raw_data():
    """Test what raw data we're getting from EmotiBit"""
    
    print("🔍 Debugging EmotiBit raw data...")
    
    # Check device status first
    response = requests.get("http://localhost:8000/api/device/status")
    status = response.json()
    print(f"📊 Device Status: {json.dumps(status, indent=2)}")
    
    print("\n" + "="*50)
    print("📊 Collecting data samples...")
    
    for i in range(10):
        print(f"\n📅 Sample {i+1}:")
        
        try:
            response = requests.get("http://localhost:8000/api/biometrics/current")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Status: {data.get('status')}")
                print(f"❤️  Heart Rate: {data.get('heart_rate')} BPM")
                print(f"📈 HRV SDNN: {data.get('hrv_sdnn')} ms")
                print(f"🌡️  Temperature: {data.get('temperature')}°C")
                print(f"⚡ EDA Level: {data.get('eda_level')}")
            else:
                print(f"❌ Error: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"❌ Request error: {e}")
        
        time.sleep(2)
    
    print("\n" + "="*50)
    print("🏥 Final health check:")
    
    try:
        response = requests.get("http://localhost:8000/health")
        health = response.json()
        print(f"📊 Health: {json.dumps(health, indent=2)}")
    except Exception as e:
        print(f"❌ Health check error: {e}")

if __name__ == "__main__":
    test_raw_data() 
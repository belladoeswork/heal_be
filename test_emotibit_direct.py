#!/usr/bin/env python3
"""
Test direct EmotiBit communication bypassing BrainFlow
"""
import asyncio
import time
from services.emotibit_direct import emotibit_direct

async def test_direct_emotibit():
    """Test direct EmotiBit connection and streaming"""
    
    print("🔄 Testing direct EmotiBit communication...")
    print("This bypasses BrainFlow and uses native EmotiBit protocol")
    print("=" * 60)
    
    try:
        # Step 1: Connect to EmotiBit
        print("🔗 Step 1: Connecting to EmotiBit...")
        connected = await emotibit_direct.connect()
        
        if not connected:
            print("❌ Failed to connect to EmotiBit")
            return False
        
        print("✅ Connected successfully!")
        
        # Show device info
        device_info = emotibit_direct.get_device_info()
        print(f"📊 Device info: {device_info}")
        
        # Step 2: Start streaming
        print("\n▶️ Step 2: Starting data streaming...")
        streaming = await emotibit_direct.start_streaming()
        
        if not streaming:
            print("❌ Failed to start streaming")
            return False
        
        print("✅ Streaming started!")
        
        # Step 3: Collect data for 30 seconds
        print("\n📊 Step 3: Collecting data for 30 seconds...")
        print("This should show REAL PPG, EDA, and Temperature data!")
        print("-" * 50)
        
        for i in range(30):
            data = emotibit_direct.get_current_data()
            
            if data:
                ppg_count = len(data.get('ppg', []))
                eda_count = len(data.get('eda', []))
                temp_count = len(data.get('temperature', []))
                accel_count = len(data.get('accelerometer', {}).get('x', []))
                
                print(f"Second {i+1:2d}: PPG={ppg_count:2d} samples, "
                      f"EDA={eda_count:2d} samples, "
                      f"Temp={temp_count:2d} samples, "
                      f"Accel={accel_count:2d} samples")
                
                # Show actual values if we have them
                if ppg_count > 0:
                    latest_ppg = data['ppg'][-1]
                    print(f"          Latest PPG: {latest_ppg:.4f}")
                
                if eda_count > 0:
                    latest_eda = data['eda'][-1]
                    print(f"          Latest EDA: {latest_eda:.4f}")
                
                if temp_count > 0:
                    latest_temp = data['temperature'][-1]
                    print(f"          Latest Temp: {latest_temp:.2f}°C")
                    
            else:
                print(f"Second {i+1:2d}: No data received")
            
            await asyncio.sleep(1)
        
        # Step 4: Final summary
        print("\n📋 Final Summary:")
        final_info = emotibit_direct.get_device_info()
        sensors = final_info.get('sensors', {})
        
        print(f"✅ Total PPG samples: {sensors.get('ppg_samples', 0)}")
        print(f"✅ Total EDA samples: {sensors.get('eda_samples', 0)}")
        print(f"✅ Total Temperature samples: {sensors.get('temperature_samples', 0)}")
        print(f"✅ Total Accelerometer samples: {sensors.get('accelerometer_samples', 0)}")
        print(f"✅ Total Gyroscope samples: {sensors.get('gyroscope_samples', 0)}")
        
        # Show final data sample
        final_data = emotibit_direct.get_current_data()
        if final_data:
            print("\n📊 Final Data Sample:")
            if final_data.get('ppg'):
                print(f"PPG: {final_data['ppg'][-5:]}")  # Last 5 values
            if final_data.get('eda'):
                print(f"EDA: {final_data['eda'][-5:]}")
            if final_data.get('temperature'):
                print(f"Temperature: {final_data['temperature'][-5:]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Cleanup
        print("\n📴 Cleaning up...")
        await emotibit_direct.disconnect()
        print("✅ Disconnected")

if __name__ == "__main__":
    success = asyncio.run(test_direct_emotibit())
    
    if success:
        print("\n🎉 SUCCESS! Direct EmotiBit communication working!")
        print("💡 This should give you REAL PPG, EDA, and Temperature data")
        print("🚀 You can now integrate this into your main application")
    else:
        print("\n❌ Direct communication failed")
        print("💡 May need to adjust the protocol commands or data format") 
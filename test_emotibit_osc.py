#!/usr/bin/env python3
"""
Test EmotiBit OSC connection to receive REAL sensor data via Oscilloscope
"""
import asyncio
from services.emotibit_osc import emotibit_osc

async def test_emotibit_osc():
    """Test EmotiBit OSC connection"""
    
    print("🔄 Testing EmotiBit OSC connection to Oscilloscope...")
    print("📋 REQUIREMENTS:")
    print("   1. ✅ EmotiBit Oscilloscope app must be running")
    print("   2. ✅ EmotiBit device connected in Oscilloscope")  
    print("   3. ✅ Click 'Record' in Oscilloscope to start streaming")
    print("   4. ✅ Enable OSC/UDP output in Oscilloscope settings")
    print("=" * 60)
    
    try:
        # Step 1: Connect to Oscilloscope
        print("🔗 Step 1: Connecting to EmotiBit Oscilloscope...")
        print("📡 Looking for OSC data on port 12345...")
        
        connected = await emotibit_osc.connect()
        
        if not connected:
            print("❌ Failed to connect to Oscilloscope")
            print("💡 Make sure:")
            print("   - EmotiBit Oscilloscope is running")
            print("   - OSC/UDP output is enabled")
            print("   - Port 12345 is available")
            return False
        
        print("✅ Connected to Oscilloscope!")
        
        # Step 2: Start streaming
        print("\n▶️ Step 2: Starting data reception...")
        streaming = await emotibit_osc.start_streaming()
        
        if not streaming:
            print("❌ Failed to start data reception")
            return False
        
        print("✅ Streaming started!")
        
        # Step 3: Listen for data for 30 seconds
        print("\n📊 Step 3: Listening for REAL sensor data for 30 seconds...")
        print("💡 If you see PPG/EDA/Temperature data, it's working!")
        print("-" * 50)
        
        for i in range(30):
            data = emotibit_osc.get_current_data()
            device_info = emotibit_osc.get_device_info()
            quality = device_info.get('data_quality', {})
            
            if data:
                ppg_count = len(data.get('ppg', []))
                eda_count = len(data.get('eda', []))
                temp_count = len(data.get('temperature', []))
                
                print(f"Second {i+1:2d}: PPG={ppg_count:2d}, EDA={eda_count:2d}, Temp={temp_count:2d} "
                      f"| Packets={quality.get('total_packets', 0)}")
                
                # Show actual values if we have them
                if ppg_count > 0:
                    latest_ppg = data['ppg'][-1]
                    print(f"          🫀 Latest PPG: {latest_ppg:.4f}")
                
                if eda_count > 0:
                    latest_eda = data['eda'][-1]
                    print(f"          ⚡ Latest EDA: {latest_eda:.4f}")
                
                if temp_count > 0:
                    latest_temp = data['temperature'][-1]
                    print(f"          🌡️  Latest Temp: {latest_temp:.2f}°C")
                    
            else:
                print(f"Second {i+1:2d}: No data received yet...")
            
            await asyncio.sleep(1)
        
        # Step 4: Final summary
        print("\n📋 Final Summary:")
        final_info = emotibit_osc.get_device_info()
        sensors = final_info.get('sensors', {})
        quality = final_info.get('data_quality', {})
        
        print(f"✅ Total PPG samples: {sensors.get('ppg_samples', 0)}")
        print(f"✅ Total EDA samples: {sensors.get('eda_samples', 0)}")
        print(f"✅ Total Temperature samples: {sensors.get('temperature_samples', 0)}")
        print(f"📊 Total packets received: {quality.get('total_packets', 0)}")
        
        if sensors.get('ppg_samples', 0) > 0:
            print("\n🎉 SUCCESS! Receiving REAL PPG data!")
        if sensors.get('eda_samples', 0) > 0:
            print("🎉 SUCCESS! Receiving REAL EDA data!")
        if sensors.get('temperature_samples', 0) > 0:
            print("🎉 SUCCESS! Receiving REAL Temperature data!")
        
        if quality.get('total_packets', 0) == 0:
            print("\n❓ No data packets received. Check:")
            print("   - EmotiBit Oscilloscope is recording (green 'Record' button)")
            print("   - OSC/UDP output is enabled in Oscilloscope settings")
            print("   - Correct IP address and port")
        
        return sensors.get('ppg_samples', 0) > 0
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Cleanup
        print("\n📴 Cleaning up...")
        await emotibit_osc.disconnect()
        print("✅ Disconnected")

if __name__ == "__main__":
    success = asyncio.run(test_emotibit_osc())
    
    if success:
        print("\n🎉 REAL EmotiBit data streaming working!")
        print("💡 You now have access to actual PPG, EDA, and Temperature!")
        print("🚀 Your frontend can get real biometric data!")
    else:
        print("\n❌ OSC connection failed")
        print("💡 Next steps:")
        print("   1. Ensure EmotiBit Oscilloscope is running")
        print("   2. Check OSC/UDP output settings in Oscilloscope")
        print("   3. Verify EmotiBit is connected and recording") 
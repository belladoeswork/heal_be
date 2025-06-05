#!/usr/bin/env python3
"""
Test the fixed EmotiBit BrainFlow connection to get REAL sensor data
"""
import asyncio
import time
from brainflow import BoardShim, BrainFlowInputParams, BoardIds, BrainFlowPresets

async def test_fixed_emotibit():
    """Test EmotiBit with corrected direct IP connection"""
    
    print("🔄 Testing FIXED EmotiBit BrainFlow connection...")
    print("📋 This should connect directly to EmotiBit and get REAL sensor data")
    print("=" * 60)
    
    # Enable debug logging
    BoardShim.enable_dev_board_logger()
    
    try:
        # Use ACTUAL EmotiBit IP address (not broadcast)
        emotibit_ip = "192.168.0.187"  # The IP from your screenshots
        
        print(f"🔗 Connecting to EmotiBit at {emotibit_ip}...")
        
        # Setup parameters with direct IP
        params = BrainFlowInputParams()
        params.ip_address = emotibit_ip  # Direct IP connection
        
        # Use EmotiBit board ID
        board_id = BoardIds.EMOTIBIT_BOARD
        board = BoardShim(board_id, params)
        
        # Connect
        board.prepare_session()
        print(f"✅ Connected successfully!")
        
        # Start streaming
        print("▶️ Starting data stream...")
        board.start_stream(45000)
        print("✅ Streaming started!")
        
        # Wait for data to accumulate
        print("⏳ Waiting 3 seconds for data...")
        await asyncio.sleep(3)
        
        # Test all presets to get different sensor data
        print("\n📊 Testing all BrainFlow presets:")
        
        presets = [
            ("DEFAULT", BrainFlowPresets.DEFAULT_PRESET, "Accelerometer, Gyroscope"),
            ("AUXILIARY", BrainFlowPresets.AUXILIARY_PRESET, "PPG Data"),
            ("ANCILLARY", BrainFlowPresets.ANCILLARY_PRESET, "EDA, Temperature"),
        ]
        
        all_data = {}
        
        for preset_name, preset, description in presets:
            try:
                print(f"\n🔍 Testing {preset_name} preset ({description}):")
                data = board.get_current_board_data(50, preset=preset)
                
                if data.shape[1] > 0:
                    print(f"✅ {preset_name}: {data.shape} - {data.shape[0]} channels, {data.shape[1]} samples")
                    all_data[preset_name] = data
                    
                    # Show actual values from first few channels
                    for ch in range(min(3, data.shape[0])):
                        if data.shape[1] > 0:
                            recent_values = data[ch][-5:]  # Last 5 values
                            avg_val = float(recent_values.mean())
                            print(f"   Channel {ch}: avg={avg_val:.4f}, recent={recent_values.tolist()}")
                            
                            # Identify sensor type by value ranges
                            if 1000 < abs(avg_val) < 100000:
                                print(f"      👆 This looks like PPG data! (values: {avg_val:.0f})")
                            elif 0 <= avg_val <= 10:
                                print(f"      👆 This looks like EDA data! (values: {avg_val:.3f})")
                            elif 20 <= avg_val <= 45:
                                print(f"      👆 This looks like Temperature data! (values: {avg_val:.1f}°C)")
                            elif -20 <= avg_val <= 20:
                                print(f"      👆 This looks like Motion data! (values: {avg_val:.3f})")
                else:
                    print(f"⭕ {preset_name}: No data")
                    all_data[preset_name] = None
                    
            except Exception as e:
                print(f"❌ {preset_name}: Error - {e}")
                all_data[preset_name] = None
        
        # Try main board data as fallback
        print(f"\n🔍 Testing main board data:")
        try:
            main_data = board.get_current_board_data(50)
            if main_data.shape[1] > 0:
                print(f"✅ MAIN: {main_data.shape}")
                all_data['MAIN'] = main_data
                
                # Analyze all channels
                for ch in range(min(10, main_data.shape[0])):
                    recent_values = main_data[ch][-5:]
                    avg_val = float(recent_values.mean())
                    print(f"   Channel {ch}: avg={avg_val:.4f}")
            else:
                print(f"⭕ MAIN: No data")
        except Exception as e:
            print(f"❌ MAIN: Error - {e}")
        
        # Analysis and recommendations
        print(f"\n📋 ANALYSIS:")
        
        total_channels = 0
        total_samples = 0
        sensor_data_found = []
        
        for preset_name, data in all_data.items():
            if data is not None:
                total_channels += data.shape[0]
                total_samples += data.shape[1]
                
                # Look for sensor patterns
                for ch in range(data.shape[0]):
                    recent_values = data[ch][-5:]
                    avg_val = float(recent_values.mean()) if len(recent_values) > 0 else 0
                    
                    if 10000 < abs(avg_val) < 100000:
                        sensor_data_found.append(f"PPG-like in {preset_name} Ch{ch}")
                    elif 0.1 <= avg_val <= 10:
                        sensor_data_found.append(f"EDA-like in {preset_name} Ch{ch}")
                    elif 20 <= avg_val <= 45:
                        sensor_data_found.append(f"Temperature-like in {preset_name} Ch{ch}")
        
        print(f"✅ Total channels found: {total_channels}")
        print(f"✅ Total samples collected: {total_samples}")
        print(f"✅ Potential sensor data: {sensor_data_found}")
        
        if sensor_data_found:
            print(f"\n🎉 SUCCESS! Found potential real sensor data:")
            for sensor in sensor_data_found:
                print(f"   📊 {sensor}")
        else:
            print(f"\n❓ No obvious sensor patterns found")
            print(f"💡 Try checking if EmotiBit is in recording mode")
        
        # Cleanup
        print(f"\n📴 Cleaning up...")
        board.stop_stream()
        board.release_session()
        print(f"✅ Test completed!")
        
        return len(sensor_data_found) > 0
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_fixed_emotibit())
    
    if success:
        print(f"\n🎉 FIXED! EmotiBit is providing real sensor data!")
        print(f"💡 The corrected BrainFlow service should now work properly")
        print(f"🚀 Your API endpoints should return real biometric values")
    else:
        print(f"\n❓ Still not getting expected sensor data")
        print(f"💡 Check if EmotiBit needs to be in specific recording mode") 
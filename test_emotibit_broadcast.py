#!/usr/bin/env python3
"""
Test EmotiBit connection using broadcast IP (the correct approach)
"""
import asyncio
import time
from brainflow import BoardShim, BrainFlowInputParams, BoardIds, BrainFlowPresets

async def test_emotibit_broadcast():
    """Test EmotiBit connection using broadcast IP"""
    
    # Enable debug logging
    BoardShim.enable_dev_board_logger()
    
    print("🔄 Testing EmotiBit with broadcast IP...")
    
    try:
        # Setup parameters with broadcast IP (the correct approach for EmotiBit)
        params = BrainFlowInputParams()
        params.ip_address = "192.168.0.255"  # Broadcast IP for network discovery
        
        # Use correct board ID
        board_id = BoardIds.EMOTIBIT_BOARD  # Should be 47
        board = BoardShim(board_id, params)
        
        print(f"📋 Board ID: {board_id}")
        print(f"📊 Sampling Rate: {BoardShim.get_sampling_rate(board_id)} Hz")
        print(f"🔗 Using broadcast IP: 192.168.0.255")
        
        # Get board description
        try:
            board_descr = BoardShim.get_board_descr(board_id)
            print(f"📝 Board Description: {board_descr}")
        except Exception as e:
            print(f"⚠️  Could not get board description: {e}")
        
        # Connect to device
        print("🔗 Connecting to EmotiBit...")
        board.prepare_session()
        print("✅ Connected successfully!")
        
        # Start streaming
        print("▶️  Starting data stream...")
        board.start_stream()
        print("🔄 Streaming started!")
        
        # Collect data for 15 seconds to test all presets
        print("📊 Collecting data for 15 seconds...")
        for i in range(15):
            time.sleep(1)
            
            try:
                # Get main data
                main_data = board.get_current_board_data(25)
                print(f"⏱️  Second {i+1}: Main data shape: {main_data.shape}")
                
                if main_data.shape[1] > 0:
                    print(f"📊 Data received: {main_data.shape[0]} channels, {main_data.shape[1]} samples")
                    
                    # Show data from each channel
                    for ch in range(min(3, main_data.shape[0])):
                        if main_data.shape[1] > 0:
                            latest_val = main_data[ch][-1]
                            print(f"📈 Channel {ch}: {latest_val:.4f}")
                
                # Test each preset
                presets_to_try = [
                    ("AUXILIARY_PRESET (PPG)", BrainFlowPresets.AUXILIARY_PRESET),
                    ("ANCILLARY_PRESET (EDA/Temp)", BrainFlowPresets.ANCILLARY_PRESET),
                    ("DEFAULT_PRESET (Accel)", BrainFlowPresets.DEFAULT_PRESET)
                ]
                
                for preset_name, preset in presets_to_try:
                    try:
                        preset_data = board.get_current_board_data(25, preset=preset)
                        if preset_data.shape[1] > 0:
                            print(f"✅ {preset_name}: {preset_data.shape}")
                            # Show some data values
                            if preset_data.shape[0] > 0 and preset_data.shape[1] > 0:
                                val = preset_data[0][-1]
                                print(f"   📊 Latest value: {val:.4f}")
                        else:
                            print(f"⭕ {preset_name}: No data")
                    except Exception as e:
                        print(f"❌ {preset_name} error: {e}")
                        
            except Exception as e:
                print(f"❌ Error getting data: {e}")
            
            print()  # Add spacing between seconds
        
        # Stop streaming and disconnect
        print("⏹️  Stopping stream...")
        board.stop_stream()
        
        print("📴 Disconnecting...")
        board.release_session()
        
        print("✅ Test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_emotibit_broadcast())
    if success:
        print("\n🎉 EmotiBit connection successful! You can now use the main application.")
    else:
        print("\n❌ EmotiBit connection failed. Check the troubleshooting guide.") 
#!/usr/bin/env python3
"""
Test script for EmotiBit connection and data streaming
"""
import asyncio
import time
from brainflow import BoardShim, BrainFlowInputParams, BoardIds, BrainFlowPresets

async def test_emotibit_connection():
    """Test EmotiBit connection and data streaming"""
    
    # Enable debug logging
    BoardShim.enable_dev_board_logger()
    
    print("🔄 Testing EmotiBit connection...")
    
    # Try different connection approaches
    connection_attempts = [
        {"description": "Auto-discovery (no IP)", "ip": None},
        {"description": "Direct IP connection", "ip": "192.168.0.187"},
        {"description": "Broadcast IP", "ip": "192.168.0.255"},
    ]
    
    for attempt in connection_attempts:
        print(f"\n🔄 Attempting: {attempt['description']}")
        
        try:
            # Setup parameters
            params = BrainFlowInputParams()
            if attempt['ip']:
                params.ip_address = attempt['ip']
                print(f"🔗 Using IP: {attempt['ip']}")
            else:
                print("🔍 Using auto-discovery")
            
            # Use correct board ID
            board_id = BoardIds.EMOTIBIT_BOARD  # Should be 47
            board = BoardShim(board_id, params)
            
            print(f"📋 Board ID: {board_id}")
            print(f"📊 Sampling Rate: {BoardShim.get_sampling_rate(board_id)} Hz")
            
            # Get board description instead of individual channels
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
            
            # Collect data for 10 seconds
            print("📊 Collecting data for 10 seconds...")
            for i in range(10):
                time.sleep(1)
                
                # Get data from different presets
                try:
                    # Get main data
                    main_data = board.get_current_board_data(25)
                    print(f"⏱️  Second {i+1}: Main data shape: {main_data.shape}")
                    
                    # Show actual data if available
                    if main_data.shape[1] > 0:
                        print(f"📊 Data received: {main_data.shape[0]} channels, {main_data.shape[1]} samples")
                        
                        # Try to identify what channels we have
                        try:
                            timestamp_channel = BoardShim.get_timestamp_channel(board_id)
                            print(f"⏰ Timestamp channel: {timestamp_channel}")
                            if main_data.shape[0] > timestamp_channel:
                                latest_timestamp = main_data[timestamp_channel][-1] if main_data.shape[1] > 0 else 0
                                print(f"🕐 Latest timestamp: {latest_timestamp}")
                        except Exception as e:
                            print(f"❓ Could not get timestamp: {e}")
                        
                        # Show first few channels
                        for ch in range(min(5, main_data.shape[0])):
                            if main_data.shape[1] > 0:
                                latest_val = main_data[ch][-1]
                                print(f"📈 Channel {ch}: {latest_val:.4f}")
                    
                    # Try different presets
                    presets_to_try = [
                        ("AUXILIARY_PRESET", BrainFlowPresets.AUXILIARY_PRESET),
                        ("ANCILLARY_PRESET", BrainFlowPresets.ANCILLARY_PRESET),
                        ("DEFAULT_PRESET", BrainFlowPresets.DEFAULT_PRESET)
                    ]
                    
                    for preset_name, preset in presets_to_try:
                        try:
                            preset_data = board.get_current_board_data(25, preset=preset)
                            if preset_data.shape[1] > 0:
                                print(f"✅ {preset_name}: {preset_data.shape}")
                            else:
                                print(f"⭕ {preset_name}: No data")
                        except Exception as e:
                            print(f"❌ {preset_name} error: {e}")
                        
                except Exception as e:
                    print(f"❌ Error getting data: {e}")
            
            # Stop streaming and disconnect
            print("⏹️  Stopping stream...")
            board.stop_stream()
            
            print("📴 Disconnecting...")
            board.release_session()
            
            print("✅ Test completed successfully!")
            return True  # Success!
            
        except Exception as e:
            print(f"❌ Connection attempt failed: {e}")
            print(f"📝 Error details: {type(e).__name__}")
            continue  # Try next connection method
    
    print("❌ All connection attempts failed!")
    return False

async def test_synthetic_board():
    """Test with synthetic board as fallback"""
    print("\n🧪 Testing synthetic board as fallback...")
    
    try:
        params = BrainFlowInputParams()
        board = BoardShim(BoardIds.SYNTHETIC_BOARD, params)
        
        print("🔗 Connecting to synthetic board...")
        board.prepare_session()
        print("✅ Synthetic board connected!")
        
        print("▶️  Starting synthetic stream...")
        board.start_stream()
        
        # Collect some data
        for i in range(3):
            time.sleep(1)
            data = board.get_current_board_data(25)
            print(f"📊 Synthetic data shape: {data.shape}")
        
        board.stop_stream()
        board.release_session()
        print("✅ Synthetic board test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Synthetic board test failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_emotibit_connection())
    
    if not success:
        print("\n🔄 Trying synthetic board...")
        asyncio.run(test_synthetic_board()) 
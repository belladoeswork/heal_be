#!/usr/bin/env python3
"""
Test EmotiBit-specific commands to start data recording
"""
import asyncio
import time
from brainflow import BoardShim, BrainFlowInputParams, BoardIds, BrainFlowPresets

async def test_emotibit_commands():
    """Test different commands to start EmotiBit data recording"""
    
    # Enable debug logging
    BoardShim.enable_dev_board_logger()
    
    print("🔄 Testing EmotiBit commands to start data recording...")
    
    try:
        # Setup parameters
        params = BrainFlowInputParams()
        # params.ip_address = "192.168.0.255"  # Use broadcast or specific IP
        
        # Use EmotiBit board
        board_id = BoardIds.EMOTIBIT_BOARD
        board = BoardShim(board_id, params)
        
        print(f"📋 Board ID: {board_id}")
        print("🔗 Connecting to EmotiBit...")
        board.prepare_session()
        print("✅ Connected successfully!")
        
        # Start streaming first (without commands)
        print("▶️ Starting basic stream...")
        board.start_stream()
        
        # Check initial data
        time.sleep(2)
        initial_data = board.get_current_board_data(10)
        print(f"📊 Initial data (before commands): {initial_data.shape}")
        
        if initial_data.shape[1] > 0:
            print("✅ Data already flowing!")
        else:
            print("❌ No data - trying EmotiBit commands...")
            
            # EmotiBit commands to try
            commands_to_try = [
                # Basic start commands
                "MR",      # Start recording
                "ML",      # Start logging  
                "MN",      # Start streaming
                "RD",      # Record data
                "SD",      # Start data
                "BEGIN",   # Begin
                "START",   # Start
                "RECORD",  # Record
                "GO",      # Go
                
                # Sensor enable commands
                "PPG_ON",
                "EDA_ON", 
                "TEMP_ON",
                "ACCEL_ON",
                "GYRO_ON",
                
                # Alternative formats
                "enable_ppg",
                "enable_eda",
                "enable_temp", 
                "enable_accel",
                "enable_all",
                
                # Numeric commands
                "1",       # Simple 1
                "255",     # Max value
                
                # EmotiBit specific (based on documentation)
                "HB",      # Heartbeat
                "TP",      # Temperature
                "EA",      # EDA
                "PG",      # PPG
                "AX",      # Accel X
                "AY",      # Accel Y  
                "AZ",      # Accel Z
                "GX",      # Gyro X
                "GY",      # Gyro Y
                "GZ",      # Gyro Z
            ]
            
            successful_commands = []
            
            for i, cmd in enumerate(commands_to_try):
                print(f"\n🔧 Trying command {i+1}/{len(commands_to_try)}: '{cmd}'")
                
                try:
                    # Send command
                    response = board.config_board(cmd)
                    print(f"📝 Response: {response}")
                    
                    # Wait for EmotiBit to process
                    time.sleep(1)
                    
                    # Check if data started flowing
                    test_data = board.get_current_board_data(10)
                    if test_data.shape[1] > 0:
                        print(f"✅ SUCCESS! Command '{cmd}' started data flow: {test_data.shape}")
                        successful_commands.append((cmd, response, test_data.shape))
                        
                        # Show some actual data
                        if test_data.shape[0] > 0:
                            for ch in range(min(3, test_data.shape[0])):
                                if test_data.shape[1] > 0:
                                    latest_val = test_data[ch][-1]
                                    print(f"   📈 Channel {ch}: {latest_val:.4f}")
                    else:
                        print(f"⭕ Command '{cmd}' - no data yet")
                        
                except Exception as e:
                    print(f"❌ Command '{cmd}' failed: {e}")
                
                # Brief pause between commands
                time.sleep(0.5)
            
            print(f"\n📋 Summary of successful commands:")
            if successful_commands:
                for cmd, response, shape in successful_commands:
                    print(f"✅ '{cmd}' -> Response: {response} -> Data: {shape}")
            else:
                print("❌ No commands successfully started data flow")
        
        # Test different presets
        print(f"\n📊 Testing different BrainFlow presets...")
        presets_to_try = [
            ("DEFAULT_PRESET", BrainFlowPresets.DEFAULT_PRESET),
            ("AUXILIARY_PRESET", BrainFlowPresets.AUXILIARY_PRESET),
            ("ANCILLARY_PRESET", BrainFlowPresets.ANCILLARY_PRESET)
        ]
        
        for preset_name, preset in presets_to_try:
            try:
                preset_data = board.get_current_board_data(25, preset=preset)
                if preset_data.shape[1] > 0:
                    print(f"✅ {preset_name}: {preset_data.shape}")
                    # Show some data values
                    if preset_data.shape[0] > 0:
                        for ch in range(min(2, preset_data.shape[0])):
                            val = preset_data[ch][-1] if preset_data.shape[1] > 0 else 0
                            print(f"   📊 Ch{ch}: {val:.4f}")
                else:
                    print(f"⭕ {preset_name}: No data")
            except Exception as e:
                print(f"❌ {preset_name} error: {e}")
        
        # Final data collection test
        print(f"\n📊 Final 5-second data collection test...")
        for i in range(5):
            time.sleep(1)
            final_data = board.get_current_board_data(25)
            print(f"⏱️ Second {i+1}: {final_data.shape}")
            
            if final_data.shape[1] > 0 and final_data.shape[0] > 0:
                # Show latest values from first few channels
                for ch in range(min(3, final_data.shape[0])):
                    val = final_data[ch][-1] if final_data.shape[1] > 0 else 0
                    print(f"   Ch{ch}: {val:.6f}")
        
        # Cleanup
        print("⏹️ Stopping stream...")
        board.stop_stream()
        print("📴 Disconnecting...")
        board.release_session()
        print("✅ Test completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_emotibit_commands()) 
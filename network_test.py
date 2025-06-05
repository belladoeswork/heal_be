#!/usr/bin/env python3
"""
Network connectivity test for EmotiBit device
"""
import socket
import time

def test_tcp_connection(host, port, timeout=5):
    """Test TCP connection to EmotiBit"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception as e:
        print(f"❌ TCP test error: {e}")
        return False

def test_udp_discovery(host, port=3131):
    """Test UDP discovery to EmotiBit"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(2)
        
        # Send discovery packet similar to BrainFlow
        message = "0,0,0,HE,1,100"
        sock.sendto(message.encode(), (host, port))
        
        try:
            response, addr = sock.recvfrom(1024)
            print(f"✅ UDP response from {addr}: {response.decode()}")
            return True
        except socket.timeout:
            print(f"⏰ No UDP response within timeout")
            return False
        finally:
            sock.close()
    except Exception as e:
        print(f"❌ UDP test error: {e}")
        return False

def ping_host(host):
    """Simple ping test"""
    import subprocess
    import platform
    
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    command = ['ping', param, '1', host]
    
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=10)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Ping error: {e}")
        return False

def main():
    emotibit_ip = "192.168.0.187"
    emotibit_port = 3131
    
    print(f"🔍 Testing network connectivity to EmotiBit at {emotibit_ip}:{emotibit_port}")
    
    # Test 1: Ping
    print(f"\n1️⃣ Testing ping to {emotibit_ip}...")
    if ping_host(emotibit_ip):
        print("✅ Ping successful - EmotiBit is reachable")
    else:
        print("❌ Ping failed - EmotiBit may not be reachable")
    
    # Test 2: TCP connection to port 3131
    print(f"\n2️⃣ Testing TCP connection to {emotibit_ip}:{emotibit_port}...")
    if test_tcp_connection(emotibit_ip, emotibit_port):
        print("✅ TCP connection successful")
    else:
        print("❌ TCP connection failed - port may not be open or different protocol")
    
    # Test 3: UDP discovery
    print(f"\n3️⃣ Testing UDP discovery to {emotibit_ip}:{emotibit_port}...")
    if test_udp_discovery(emotibit_ip, emotibit_port):
        print("✅ UDP discovery successful")
    else:
        print("❌ UDP discovery failed")
    
    # Test 4: Try different ports that EmotiBit might be using
    print(f"\n4️⃣ Testing other common ports...")
    test_ports = [3000, 3131, 12345, 8080, 80]
    for port in test_ports:
        print(f"  📡 Testing port {port}...", end=" ")
        if test_tcp_connection(emotibit_ip, port, timeout=2):
            print("✅ Open")
        else:
            print("❌ Closed/No response")

if __name__ == "__main__":
    main() 
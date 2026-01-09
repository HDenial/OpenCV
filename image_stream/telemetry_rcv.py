#recieves telemetry data from multiple TCP sockets and prints the latest values.

import time
import socket
import threading
import json

# IP of the ROS2 server
HOST = '192.168.0.57' #'127.0.0.1'  

# Ports for different streams
PORTS = {
    6000: 'atmos',
    6001: 'lidar',
    6002: 'orientation',
    6003: 'rpm',
}

# Store latest data per stream
latest_data = {
    'atmos': None,
    'lidar': None,
    'orientation': None,
    'rpm': None,
}

# Lock to safely update shared data
data_lock = threading.Lock()

def receive_message(sock):
    raw_len = sock.recv(4)
    if not raw_len:
        return None
    msg_len = int.from_bytes(raw_len, byteorder='big')

    data = b''
    while len(data) < msg_len:
        chunk = sock.recv(msg_len - len(data))
        if not chunk:
            return None
        data += chunk
    try:
        return json.loads(data.decode('utf-8'))
    except Exception as e:
        print(f"JSON decode error: {e}")
        return None

def socket_listener(port, label):
    while True:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((HOST, port))
                print(f"[{label}] Connected to {HOST}:{port}")

                while True:
                    message = receive_message(sock)
                    if message is None:
                        print(f"[{label}] Disconnected")
                        break

                    with data_lock:
                        latest_data[label] = message
                        print(f"[{label}] {message}")

        except Exception as e:
            print(f"[{label}] Error: {e}")
            print(f"[{label}] Reconnecting in 2s...")
            import time
            time.sleep(2)

# Start a thread for each port
for port, label in PORTS.items():
    t = threading.Thread(target=socket_listener, args=(port, label), daemon=True)
    t.start()

# Main thread stays alive
try:
    while True:
        with data_lock:
            
            atmos = latest_data['atmos']
            if atmos:
                print("Current pressure:", atmos.get('pressure'), "Temperature:", atmos.get('temperature'))
            
            lidar = latest_data['lidar']
            if lidar:
                print("Current lidar data:", lidar.get('back_left'))
            
            orientation = latest_data['orientation']
            if orientation:
                print("Current orientation data:", orientation['gps'].get('latitude'))
            
            rpm = latest_data['rpm']
            if rpm:
                print("Current RPM data:", rpm.get('left'), rpm.get('right'))

        
        time.sleep(1)
except KeyboardInterrupt:
    print("Shutting down.")

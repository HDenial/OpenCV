# Client code to receive and display images/video feed over TCP sockets.

import socket
import struct
import cv2
import numpy as np
import threading
import time

def receive_images(ip, port, window_name):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((ip, port))
    print(f'Connected to {window_name} at {ip}:{port}')

    data = b""
    payload_size = struct.calcsize('>L')

    while True:
        # Read message length
        while len(data) < payload_size:
            packet = sock.recv(4096)
            if not packet:
                print(f'{window_name} connection closed by server')
                return
            data += packet

        packed_msg_size = data[:payload_size]
        data = data[payload_size:]
        msg_size = struct.unpack('>L', packed_msg_size)[0]

        # Read image data based on length
        while len(data) < msg_size:
            packet = sock.recv(4096)
            if not packet:
                print(f'{window_name} connection closed by server')
                return
            data += packet

        frame_data = data[:msg_size]
        data = data[msg_size:]

        # Decode and show image
        img_array = np.frombuffer(frame_data, dtype=np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        if img is not None:
            cv2.imshow(window_name, img)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        else:
            print(f'Failed to decode {window_name} image')

    sock.close()
    cv2.destroyWindow(window_name)

def main():
    server_ip = '192.168.0.57'  #server's LAN IP

    front_thread = threading.Thread(target=receive_images, args=(server_ip, 5000, 'Front Camera'))
    back_thread = threading.Thread(target=receive_images, args=(server_ip, 5001, 'Back Camera'))

    front_thread.start()
    back_thread.start()

    front_thread.join()
    back_thread.join()

if __name__ == '__main__':
    main()
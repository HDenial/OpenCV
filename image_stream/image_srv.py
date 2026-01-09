#!/usr/bin/env python3

# Streams images/video from three ROS2 camera topics over TCP sockets.
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import socket
import cv2
import struct
import threading
import queue

class CameraServer(Node):
    def __init__(self):
        super().__init__('camera_server')
        self.bridge = CvBridge()

        # Queues for images (latest frame only)
        self.front_image_queue = queue.Queue(maxsize=1)
        self.back_image_queue = queue.Queue(maxsize=1)
        self.rot_image_queue = queue.Queue(maxsize=1)

        # Start socket worker threads
        self.front_thread = threading.Thread(
            target=self.socket_worker,
            args=(5000, 'Front Camera', self.front_image_queue),
            daemon=True
        )
        self.back_thread = threading.Thread(
            target=self.socket_worker,
            args=(5001, 'Back Camera', self.back_image_queue),
            daemon=True
        )
        self.rot_thread = threading.Thread(
            target=self.socket_worker,
            args=(5002, 'Rotating Camera', self.rot_image_queue),
            daemon=True
        )
        self.front_thread.start()
        self.back_thread.start()
        self.rot_thread.start()

        # Subscriptions
        self.create_subscription(Image, '/camera/image_raw', self.front_image_callback, 60)
        self.create_subscription(Image, '/camera/image_raw_b', self.back_image_callback, 60)
        self.create_subscription(Image, '/camera/image_raw_r', self.rot_image_callback, 60)

    def front_image_callback(self, msg):
        self.enqueue_latest_image(msg, self.front_image_queue, 'Front Camera')

    def back_image_callback(self, msg):
        self.enqueue_latest_image(msg, self.back_image_queue, 'Back Camera')

    def rot_image_callback(self, msg):
        self.enqueue_latest_image(msg, self.rot_image_queue, 'Rotating Camera')

    def enqueue_latest_image(self, msg, q, label):
        try:
            img = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
            # Replace previous image if queue is full
            if not q.empty():
                try:
                    q.get_nowait()
                except queue.Empty:
                    pass
            q.put_nowait(img)
        except Exception as e:
            self.get_logger().error(f'{label} callback error: {e}')

    def socket_worker(self, port, label, image_queue):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('', port))
        sock.listen(1)
        self.get_logger().info(f'{label} server listening on port {port}')

        while rclpy.ok():
            try:
                self.get_logger().info(f'{label}: Waiting for client connection...')
                conn, addr = sock.accept()
                self.get_logger().info(f'{label}: Client connected from {addr}')

                while rclpy.ok():
                    try:
                        img = image_queue.get(timeout=0.1)  # wait for image
                    except queue.Empty:
                        continue

                    _, buffer = cv2.imencode('.jpg', img)
                    data = buffer.tobytes()
                    length = struct.pack('>L', len(data))

                    try:
                        conn.sendall(length + data)
                        # self.get_logger().info(f'{label}: Sent image of {len(data)} bytes')
                    except (BrokenPipeError, ConnectionResetError):
                        self.get_logger().warn(f'{label}: Client disconnected')
                        conn.close()
                        break
            except Exception as e:
                self.get_logger().error(f'{label} socket error: {e}')
                try:
                    conn.close()
                except:
                    pass  # might not be open
        sock.close()

def main(args=None):
    rclpy.init(args=args)
    node = CameraServer()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('Shutting down camera server...')
    finally:
        rclpy.shutdown()

if __name__ == '__main__':
    main()

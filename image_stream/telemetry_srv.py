#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64
from sensor_msgs.msg import NavSatFix, Imu, Range, PointCloud2, BatteryState, Joy
from custom_boat.msg import Orientation, Rpm, Atmos, Lidar
import json
from dataclasses import asdict
import socket
import struct
import threading
import queue

# json serialization utils
def std_float_to_data(msg):
    return msg.data if hasattr(msg, 'data') else msg

def navsatfix_to_dict(msg):
    return {
        'latitude': msg.latitude,
        'longitude': msg.longitude,
        'altitude': msg.altitude,
        'covariance': list(msg.position_covariance),
        'cov_type': msg.position_covariance_type,
    }
def joy_to_dict(msg):
    return {
        'axes': list(msg.axes),
        'buttons': list(msg.buttons),

    }
def imu_to_dict(msg):
    return {
        'orientation': {
            'x': msg.orientation.x,
            'y': msg.orientation.y,
            'z': msg.orientation.z,
            'w': msg.orientation.w,
        },
        'angular_velocity': {
            'x': msg.angular_velocity.x,
            'y': msg.angular_velocity.y,
            'z': msg.angular_velocity.z,
        },
        'linear_acceleration': {
            'x': msg.linear_acceleration.x,
            'y': msg.linear_acceleration.y,
            'z': msg.linear_acceleration.z,
        },
    }

def range_to_dict(msg):
    return {
        'range': msg.range,
        'min': msg.min_range,
        'max': msg.max_range,
        'field_of_view': msg.field_of_view,
    }

def battery_to_dict(msg):
    return {
        'voltage': msg.voltage,
        'current': msg.current,
        'charge': msg.charge,
        'capacity': msg.capacity,
        'percentage': msg.percentage,
        'power_supply_status': msg.power_supply_status,
    }

def orientation_to_dict(msg):
    return {
        'gps': navsatfix_to_dict(msg.gps),
        'imu': imu_to_dict(msg.imu),
        'compass': std_float_to_data(msg.compass),
        'cog': std_float_to_data(msg.cog),
        'sog': std_float_to_data(msg.sog),
        'rudder_pos': std_float_to_data(msg.rudder_pos),
        'battery': battery_to_dict(msg.battery),
    }

def rpm_to_dict(msg):
    return {
        'left': std_float_to_data(msg.left),
        'right': std_float_to_data(msg.right),
        'joy': joy_to_dict(msg.joy)
    }

def atmos_to_dict(msg):
    return {
        'pressure': std_float_to_data(msg.pressure),
        'temperature': std_float_to_data(msg.temperature),
        'wind_speed': std_float_to_data(msg.w_speed),
        'wind_direction': std_float_to_data(msg.w_direction),
    }

def lidar_to_dict(msg):
    return {
        'back_left': range_to_dict(msg.back_left),
        'back_right': range_to_dict(msg.back_right),
        'front_left': range_to_dict(msg.front_left),
        'front_right': range_to_dict(msg.front_right),
        'down': range_to_dict(msg.down),
        'radar': 'not_serialized',  # PointCloud2 is hard to serialize to JSON
    }

class Float64StreamServer(Node):
    def __init__(self):
        super().__init__('float64_stream_server')

        # Initialize last values for pressure and temperature
        self.last_pressure = Float64(data=1013.25)
        self.last_temperature = Float64(data=24.0)
        self.last_cog = Float64(data=float('nan'))
        self.last_sog = Float64(data=float('nan'))
        self.last_rudder = Float64(data=float('0'))
        self.last_wind_speed = Float64(data=float('0'))
        self.last_wind_direction = Float64(data=float('0'))
        self.last_imu = Imu()
        self.last_gps = NavSatFix()
        self.last_bl= Range()
        self.last_br = Range()
        self.last_fl = Range()
        self.last_fr = Range()
        self.last_down = Range()
        self.last_battery = BatteryState()
        self.last_Joy = Joy()

        # Queues for latest full messages (maxsize=1)
        self.atmos_queue = queue.Queue(maxsize=1)
        self.lidar_queue = queue.Queue(maxsize=1)
        self.orientation_queue = queue.Queue(maxsize=1)
        self.rpm_queue = queue.Queue(maxsize=1)

        # Queues for individual sensor data
        self.pressure_queue = queue.Queue(maxsize=1)
        self.temperature_queue = queue.Queue(maxsize=1)
        self.rpm_left_queue = queue.Queue(maxsize=1)
        self.rpm_right_queue = queue.Queue(maxsize=1)
        self.wind_speed_queue = queue.Queue(maxsize=1)
        self.wind_direction_queue = queue.Queue(maxsize=1)
        self.cog_queue = queue.Queue(maxsize=1)
        self.sog_queue = queue.Queue(maxsize=1)
        self.compass_queue = queue.Queue(maxsize=1)
        self.gps_queue = queue.Queue(maxsize=1)
        self.imu_queue = queue.Queue(maxsize=1)
        self.lidar_back_left_queue = queue.Queue(maxsize=1)
        self.lidar_back_right_queue = queue.Queue(maxsize=1)
        self.lidar_front_left_queue = queue.Queue(maxsize=1)
        self.lidar_front_right_queue = queue.Queue(maxsize=1)
        self.lidar_down_queue = queue.Queue(maxsize=1)
        self.radar_queue = queue.Queue(maxsize=1)
        self.rudder_pos_queue = queue.Queue(maxsize=1)
        self.battery_queue = queue.Queue(maxsize=1)
        self.joy_queue = queue.Queue(maxsize=1)

        

        # Start socket worker threads
        self.thread1 = threading.Thread(
            target=self.socket_worker,
            args=(6000, 'Atmospheric', self.atmos_queue),
            daemon=True
        )
        self.thread2 = threading.Thread(
            target=self.socket_worker,
            args=(6001, 'Lidar', self.lidar_queue),
            daemon=True
        )

        self.thread3 = threading.Thread(
            target=self.socket_worker,
            args=(6002, 'Orientation', self.orientation_queue),
            daemon=True
        )
        self.thread4 = threading.Thread(
            target=self.socket_worker,
            args=(6003, 'RPM', self.rpm_queue),
            daemon=True
        )

        for i in range(1, 5):
            getattr(self, f"thread{i}").start()


        # Subscriptions
        self.create_subscription(Float64, '/atmos/pressure', self.pressure_callback, 10)
        self.create_subscription(Float64, '/atmos/temperature', self.temperature_callback, 10)
        self.create_subscription(Float64, '/engine_rpm/left', self.rpm_left_callback, 10)
        self.create_subscription(Float64, '/engine_rpm/right', self.rpm_right_callback, 10)
        self.create_subscription(Float64, '/mero/apparent_wind/magnitude', self.wind_speed_callback, 10)
        self.create_subscription(Float64, '/mero/apparent_wind/direction', self.wind_direction_callback, 10)
        self.create_subscription(Float64, '/mero/cog', self.cog_callback, 10)
        self.create_subscription(Float64, '/mero/sog', self.sog_callback, 10)
        self.create_subscription(Float64, '/mero/heading', self.compass_callback, 10)
        self.create_subscription(NavSatFix, '/mero/gps', self.gps_callback, 10)
        self.create_subscription(Imu, '/mero/imu', self.imu_callback, 10)
        self.create_subscription(Range, '/mero/lidar/back/left', self.lidar_back_left_callback, 10)
        self.create_subscription(Range, '/mero/lidar/back/right', self.lidar_back_right_callback, 10)
        self.create_subscription(Range, '/mero/lidar/front/left', self.lidar_front_left_callback, 10)
        self.create_subscription(Range, '/mero/lidar/front/right', self.lidar_front_right_callback, 10)
        self.create_subscription(Range, '/mero/lidar/down', self.lidar_down_callback, 10)
        self.create_subscription(PointCloud2, '/mero/lidar/pointcloud', self.radar_callback, 10)
        self.create_subscription(Float64, '/mero/rudder/left/cmd_pos', self.rudder_pos_callback, 10)
        self.create_subscription(BatteryState, '/mero/battery_state', self.battery_callback, 10)
        self.create_subscription(Joy, '/joy_filtered', self.joy_callback, 10)

        # update full message contents
        self.create_timer(0.1, self.update_orientation_message)
        self.create_timer(0.1, self.update_rpm_message)
        self.create_timer(0.1, self.update_atmospheric_message)
        self.create_timer(0.1, self.update_lidar_message)

    #create broad message types for each value then callback functions

    def pressure_callback(self, msg):
        self.replace_queue(msg, self.pressure_queue, 'Pressure')

    def temperature_callback(self, msg):
        self.replace_queue(msg, self.temperature_queue, 'Temperature')

    def rpm_left_callback(self, msg):
        self.replace_queue(msg, self.rpm_left_queue, 'RPM Left')

    def rpm_right_callback(self, msg):
        self.replace_queue(msg, self.rpm_right_queue, 'RPM Right')

    def wind_speed_callback(self, msg):
        self.replace_queue(msg, self.wind_speed_queue, 'Wind Speed')

    def wind_direction_callback(self, msg):
        self.replace_queue(msg, self.wind_direction_queue, 'Wind Direction')

    def cog_callback(self, msg):
        self.replace_queue(msg, self.cog_queue, 'COG')

    def sog_callback(self, msg):
        self.replace_queue(msg, self.sog_queue, 'SOG')

    def compass_callback(self, msg):
        self.replace_queue(msg, self.compass_queue, 'Compass')

    def gps_callback(self, msg):
        self.replace_queue(msg, self.gps_queue, 'GPS')

    def imu_callback(self, msg):
        self.replace_queue(msg, self.imu_queue, 'IMU')

    def lidar_back_left_callback(self, msg):
        self.replace_queue(msg, self.lidar_back_left_queue, 'Lidar Back Left')

    def lidar_back_right_callback(self, msg):
        self.replace_queue(msg, self.lidar_back_right_queue, 'Lidar Back Right')

    def lidar_front_left_callback(self, msg):
        self.replace_queue(msg, self.lidar_front_left_queue, 'Lidar Front Left')

    def lidar_front_right_callback(self, msg):
        self.replace_queue(msg, self.lidar_front_right_queue, 'Lidar Front Right')

    def lidar_down_callback(self, msg):
        self.replace_queue(msg, self.lidar_down_queue, 'Lidar Down')

    def radar_callback(self, msg):
        self.replace_queue(msg, self.radar_queue, 'Radar')
    
    def rudder_pos_callback(self, msg):
        self.replace_queue(msg, self.rudder_pos_queue, 'Rudder Position')

    def battery_callback(self, msg):
        self.replace_queue(msg, self.battery_queue, 'Battery State')

    def joy_callback(self, msg):
        self.replace_queue(msg, self.joy_queue, 'Joy')

    def enqueue_latest_value(self, msg, q, label):
        try:
            if not q.empty():
                try:
                    q.get_nowait()
                except queue.Empty:
                    pass
            q.put_nowait(msg.data)
        except Exception as e:
            self.get_logger().error(f'{label} callback error: {e}')

    def replace_queue(self, msg, q, label):
        try:
            if not q.empty():
                try:
                    q.get_nowait()
                except queue.Empty:
                    pass
            q.put_nowait(msg)
        except Exception as e:
            self.get_logger().error(f'{label} callback error: {e}')

    def update_orientation_message(self):

        msg = Orientation()

        try:
            msg.gps = self.gps_queue.get_nowait()
            self.last_gps = msg.gps
        except queue.Empty:
            msg.gps = self.last_gps

        try:
            msg.imu = self.imu_queue.get_nowait()
            self.last_imu = msg.imu
        except queue.Empty:
            msg.imu = self.last_imu

        try:
            msg.compass = self.compass_queue.get_nowait()
        except queue.Empty:
            msg.compass = Float64(data=float('nan'))

        try:
            msg.cog = self.cog_queue.get_nowait()
            self.last_cog = msg.cog.data
        except queue.Empty:
            msg.cog = self.last_cog

        try:
            msg.sog = self.sog_queue.get_nowait()
            self.last_sog = msg.sog.data
        except queue.Empty:
            msg.sog = self.last_sog
        
        try:
            msg.rudder_pos = self.rudder_pos_queue.get_nowait()
            self.last_rudder = msg.rudder_pos.data
        except queue.Empty:
            msg.rudder_pos = self.last_rudder

        try:
            msg.battery = self.battery_queue.get_nowait()
            self.last_battery = msg.battery
        except queue.Empty:
            msg.battery = self.last_battery

        # Always push the most recent available msg
        if not self.orientation_queue.full():
            self.orientation_queue.put_nowait(msg)

    def update_rpm_message(self): 
        msg = Rpm()
        try: 
            msg.left = self.rpm_left_queue.get_nowait()
            msg.right = self.rpm_right_queue.get_nowait()
        except queue.Empty:
            pass
        try:
            msg.joy = self.joy_queue.get_nowait()
            self.last_Joy = msg.joy
        except queue.Empty:
            msg.joy = self.last_Joy
        if not self.rpm_queue.full():
            self.rpm_queue.put_nowait(msg)


    def update_atmospheric_message(self):
        msg = Atmos()
        try:
            msg.pressure = self.pressure_queue.get_nowait()
            self.last_pressure = msg.pressure
        except queue.Empty:
            msg.pressure = self.last_pressure

        try:
            msg.temperature = self.temperature_queue.get_nowait()
            self.last_temperature = msg.temperature
        except queue.Empty:
            msg.temperature = self.last_temperature

        try:
            msg.w_speed = self.wind_speed_queue.get_nowait()
            self.last_wind_speed = msg.w_speed
        except queue.Empty:
            msg.w_speed = self.last_wind_speed

        try:
            msg.w_direction = self.wind_direction_queue.get_nowait()
            self.last_wind_direction = msg.w_direction
        except queue.Empty:
            msg.w_direction = self.last_wind_direction

        if not self.atmos_queue.full():
            self.atmos_queue.put_nowait(msg)

    def update_lidar_message(self):
        lidar = Lidar()

        try:
            lidar.back_left = self.lidar_back_left_queue.get_nowait()
            self.last_bl = lidar.back_left
        except queue.Empty:
            lidar.back_left = self.last_bl

        try:
            lidar.back_right = self.lidar_back_right_queue.get_nowait()
            self.last_br = lidar.back_right
        except queue.Empty:
            lidar.back_right = self.last_br


        try:
            lidar.front_left = self.lidar_front_left_queue.get_nowait()
            self.last_fl = lidar.front_left
        except queue.Empty:
            lidar.front_left = self.last_fl


        try:
            lidar.front_right = self.lidar_front_right_queue.get_nowait()
            self.last_fr = lidar.front_right
        except queue.Empty:
            lidar.front_right = self.last_fr

        try:
            lidar.down = self.lidar_down_queue.get_nowait()
            self.last_down = lidar.down
        except queue.Empty:
            lidar.down = self.last_down

        try:
            lidar.radar = self.radar_queue.get_nowait()
        except queue.Empty:
            lidar.radar = PointCloud2()

        if not self.lidar_queue.full():
            self.lidar_queue.put_nowait(lidar)


    def socket_worker(self, port, label, value_queue):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('', port))
        sock.listen(1)
        self.get_logger().info(f'{label} server listening on port {port}')

        # Pick a serializer based on the label
        serializers = {
            'Orientation': orientation_to_dict,
            'RPM': rpm_to_dict,
            'Atmospheric': atmos_to_dict,
            'Lidar': lidar_to_dict,
        }
        serializer = serializers.get(label, lambda x: {"error": "No serializer"})

        while rclpy.ok():
            try:
                self.get_logger().info(f'{label}: Waiting for client connection...')
                conn, addr = sock.accept()
                self.get_logger().info(f'{label}: Client connected from {addr}')

                while rclpy.ok():
                    try:
                        value = value_queue.get(timeout=0.1)
                    except queue.Empty:
                        continue

                    try:
                        dict_data = serializer(value)
                        json_str = json.dumps(dict_data)
                        json_bytes = json_str.encode('utf-8')

                        # Send length of JSON first (fixed 4 bytes)
                        conn.sendall(len(json_bytes).to_bytes(4, byteorder='big'))
                        # Then send actual JSON data
                        conn.sendall(json_bytes)

                    except (BrokenPipeError, ConnectionResetError):
                        self.get_logger().warn(f'{label}: Client disconnected')
                        conn.close()
                        break
            except Exception as e:
                self.get_logger().error(f'{label} socket error: {e}')
                try:
                    conn.close()
                except:
                    pass
        sock.close()


def main(args=None):
    rclpy.init(args=args)
    node = Float64StreamServer()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('Shutting down Float64 stream server...')
    finally:
        rclpy.shutdown()

if __name__ == '__main__':
    main()
#!/usr/bin/env python3

import base64
import socket
import threading
import time

import rclpy
from rclpy.node import Node
from std_msgs.msg import String, UInt8MultiArray


class NtripClientNode(Node):

    def __init__(self):
        super().__init__('ntrip_client_node')

        # Declare parameters
        self.declare_parameter('ntrip_address', '')
        self.declare_parameter('ntrip_port', 2101)
        self.declare_parameter('ntrip_username', '')
        self.declare_parameter('ntrip_password', '')
        self.declare_parameter('ntrip_mountpoint', '')

        # Get parameters
        self.address = self.get_parameter('ntrip_address').value
        self.port = self.get_parameter('ntrip_port').value
        self.username = self.get_parameter('ntrip_username').value
        self.password = self.get_parameter('ntrip_password').value
        self.mountpoint = self.get_parameter('ntrip_mountpoint').value

        # GGA data (properly initialized to None)
        self.gngga = None
        self.gngga_lock = threading.Lock()

        # Socket
        self.sock = None

        # Publisher / Subscriber
        self.pub_rtcm = self.create_publisher(UInt8MultiArray, '/ntrip_rtcm', 10)
        self.sub_gngga = self.create_subscription(
            String, '/gngga', self.gngga_callback, 10)

        # Connection flag
        self.connected = False
        self.running = True

        # Start NTRIP communication in a separate thread
        self.ntrip_thread = threading.Thread(target=self.ntrip_loop, daemon=True)
        self.ntrip_thread.start()

    def gngga_callback(self, msg):
        with self.gngga_lock:
            self.gngga = msg.data

    def build_ntrip_header(self):
        credentials = '{}:{}'.format(self.username, self.password)
        pwd = base64.b64encode(credentials.encode('ascii')).decode('ascii')

        header = (
            'GET /{} HTTP/1.1\r\n'
            'Host: {}\r\n'
            'Ntrip-Version: Ntrip/2.0\r\n'
            'User-Agent: NTRIP ROS2Client/1.0\r\n'
            'Accept: */*\r\n'
            'Connection: close\r\n'
            'Authorization: Basic {}\r\n'
            '\r\n'
        ).format(self.mountpoint, self.address, pwd)

        return header.encode('ascii')

    def connect(self):
        """Establish connection to NTRIP server. Returns True on success."""
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(10.0)
            self.sock.connect((self.address, int(self.port)))

            header = self.build_ntrip_header()
            self.sock.sendall(header)

            resp = self.sock.recv(4096).decode('ascii', errors='replace')

            if resp.startswith('STREAMTABLE'):
                self.get_logger().error(
                    'Invalid or no mountpoint: {}'.format(self.mountpoint))
                self.close_socket()
                return False
            elif 'HTTP/1.1 200' not in resp and 'ICY 200' not in resp:
                self.get_logger().error(
                    'NTRIP server responded with: {}'.format(resp.strip()))
                self.close_socket()
                return False

            self.get_logger().info(
                'Connected to NTRIP server {}:{}/{}'.format(
                    self.address, self.port, self.mountpoint))
            self.connected = True
            return True

        except socket.error as e:
            self.get_logger().error(
                'Failed to connect to NTRIP server: {}'.format(e))
            self.close_socket()
            return False

    def close_socket(self):
        self.connected = False
        if self.sock is not None:
            try:
                self.sock.close()
            except socket.error:
                pass
            self.sock = None

    def ntrip_loop(self):
        """Main loop running in a separate thread."""
        reconnect_interval = 5.0

        while self.running:
            # Connect if not connected
            if not self.connected:
                self.get_logger().info(
                    'Connecting to NTRIP server {}:{}...'.format(
                        self.address, self.port))
                if not self.connect():
                    self.get_logger().warn(
                        'Reconnecting in {} seconds...'.format(
                            int(reconnect_interval)))
                    time.sleep(reconnect_interval)
                    continue

            # Send GGA to server if available
            with self.gngga_lock:
                gga = self.gngga

            if gga is not None:
                try:
                    # ublox_gnss_driver strips trailing \r\n from GGA;
                    # NTRIP server expects NMEA sentences ending with \r\n
                    gga_line = gga if gga.endswith('\r\n') else gga + '\r\n'
                    self.sock.sendall(gga_line.encode('ascii'))
                except socket.error as e:
                    self.get_logger().warn(
                        'Failed to send GGA: {}'.format(e))
                    self.close_socket()
                    continue

            # Receive RTCM data
            try:
                self.sock.settimeout(5.0)
                data = self.sock.recv(4096)
                if len(data) == 0:
                    self.get_logger().warn('Connection closed by server.')
                    self.close_socket()
                    continue

                # Publish raw bytes as UInt8MultiArray
                msg = UInt8MultiArray()
                msg.data = list(data)
                self.pub_rtcm.publish(msg)

            except socket.timeout:
                # No data received within timeout, loop back
                continue
            except socket.error as e:
                self.get_logger().warn(
                    'Socket error during receive: {}'.format(e))
                self.close_socket()
                continue

    def destroy_node(self):
        self.running = False
        self.close_socket()
        if self.ntrip_thread.is_alive():
            self.ntrip_thread.join(timeout=3.0)
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = NtripClientNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()

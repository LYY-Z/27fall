#!/usr/bin/env python3
# coding: UTF-8

import rclpy
from rclpy.node import Node
import serial
import time
from nav_msgs.msg import Odometry
from builtin_interfaces.msg import Time as TimeMsg

Bytenum_vel = 0
Bytenum_dir = 0
last_pose = 0
C = 227.45 / 1000


def DueVelData(inputdata):
    global Bytenum_vel
    for data in inputdata:
        if data == 0x01 and Bytenum_vel == 0:
            Bytenum_vel = 1
            continue
        if data == 0x03 and Bytenum_vel == 1:
            Bytenum_vel = 2
            continue
        if data == 0x02 and Bytenum_vel == 2:
            Bytenum_vel = 3
            continue
        if Bytenum_vel == 3:
            data_high = data
            Bytenum_vel = 4
            continue
        if Bytenum_vel == 4:
            data_low = data
            Bytenum_vel = 0
            Angle_vel = data_high * 256 + data_low
            return float(Angle_vel)


def DueDirData(inputdata):
    global Bytenum_dir
    global last_pose
    for data in inputdata:
        if data == 0x01 and Bytenum_dir == 0:
            Bytenum_dir = 1
            continue
        if data == 0x03 and Bytenum_dir == 1:
            Bytenum_dir = 2
            continue
        if data == 0x02 and Bytenum_dir == 2:
            Bytenum_dir = 3
            continue
        if Bytenum_dir == 3:
            data_high = data
            Bytenum_dir = 4
            continue
        if Bytenum_dir == 4:
            data_low = data
            Bytenum_dir = 0
            position = data_high * 256 + data_low
            pose = position - last_pose
            last_pose = position
            if (pose >= 0 and pose < 512) or (pose > -1024 and pose < -512):
                direction = 1
            elif (pose < 0 and pose > -512) or (pose < 1024 and pose > 512):
                direction = -1
            else:
                direction = 1
            return int(direction)


class EncoderVelNode(Node):
    def __init__(self):
        super().__init__('encoder_vel')
        self.pub = self.create_publisher(Odometry, 'encoder', 10)
        self.declare_parameter('serial_port', '/dev/encoder')
        self.declare_parameter('baud_rate', 57600)
        self.declare_parameter('k', 1.0)
        port = self.get_parameter('serial_port').get_parameter_value().string_value
        baud = self.get_parameter('baud_rate').get_parameter_value().integer_value
        self.k = self.get_parameter('k').get_parameter_value().double_value
        self.ser = serial.Serial(port, baud)
        self.get_logger().info(f"Serial port open: {self.ser.is_open}")
        timer_period = 0.02  # 20ms
        self.timer = self.create_timer(timer_period, self.timer_callback)

    def timer_callback(self):
        send_data = bytes.fromhex('01 03 00 03 00 01 74 0A')
        self.ser.write(send_data)
        datahex = self.ser.read(7)
        angle_v = DueVelData(datahex)
        send_data = bytes.fromhex('01 03 00 00 00 01 84 0A')
        self.ser.write(send_data)
        datahex = self.ser.read(7)
        dir = DueDirData(datahex)
        if angle_v is None or dir is None:
            self.get_logger().warn("Failed to parse encoder data.")
            return
        Vel = angle_v * dir * C / 1024.0 / 0.02 * self.k
        pub_vel = Odometry()
        pub_vel.header.frame_id = 'odom'
        pub_vel.child_frame_id = 'base_footprint'
        pub_vel.header.stamp = self.get_clock().now().to_msg()
        pub_vel.twist.twist.linear.x = Vel
        self.pub.publish(pub_vel)

def main(args=None):
    rclpy.init(args=args)
    node = EncoderVelNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()

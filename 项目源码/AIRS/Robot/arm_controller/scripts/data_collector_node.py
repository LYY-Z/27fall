#!/usr/bin/env python
import rospy
import csv
import os
from sensor_msgs.msg import JointState
from geometry_msgs.msg import Pose2D
import time
from collections import deque


class DataCollector:
    def __init__(self):
        rospy.init_node('data_collector', anonymous=True)

        # 从launch文件获取参数
        self.csv_directory = rospy.get_param('~csv_directory', os.getcwd()) # 默认为当前工作目录
        self.duration_threshold = rospy.get_param('~duration_threshold', 10.0) # 默认10秒
        self.joint_zero_threshold = rospy.get_param('~joint_zero_threshold', 0.01) # 默认0.01弧度
        self.rate = rospy.get_param('~rate', 100) # 数据采集频率，默认100Hz
        self.num_joints = rospy.get_param('~collect_arm_joint_num', 4) # 默认4个关节

        # 初始化数据存储
        self.left_joint_state = None
        self.right_joint_state = None
        # self.base_vel = None
        self.base_pos = None
        self.start_time = time.time()
        self.stopped_recently = deque(maxlen=100) # 记录最近100次检查的停止状态 (100次 * 0.01s = 1s)
        self.all_data_received = False # 标志位，确保所有数据都已收到

        # 订阅话题
        rospy.Subscriber("/left/Arm/JointState", JointState, self.joint_state_left_callback)
        rospy.Subscriber("/right/Arm/JointState", JointState, self.joint_state_right_callback)
        # rospy.Subscriber("/controller_vel", Pose2D, self.base_vel_callback)
        rospy.Subscriber("/controller_pos", Pose2D, self.base_pos_callback)

        # 确保CSV目录存在
        os.makedirs(self.csv_directory, exist_ok=True)
        # CSV文件
        self.csv_filename = os.path.join(self.csv_directory, f"robot_data_{int(self.start_time)}.csv")
        self.csv_file = open(self.csv_filename, 'w', newline='')
        self.csv_writer = csv.writer(self.csv_file)
        # 写入CSV头部
        # 动态生成包含指定数量关节列的头部
        header = ['timestamp'] # 统一时间戳
        # 左臂关节: position (num_joints列) + velocity (num_joints列)
        header.extend([f'left_joint_pos_{i+1}' for i in range(self.num_joints)])
        header.extend([f'left_joint_vel_{i+1}' for i in range(self.num_joints)])
        # 右臂关节: position (num_joints列) + velocity (num_joints列)
        header.extend([f'right_joint_pos_{i+1}' for i in range(self.num_joints)])
        header.extend([f'right_joint_vel_{i+1}' for i in range(self.num_joints)])
        # 基座速度
        # header.extend(['base_vel_x', 'base_vel_y', 'base_vel_theta'])
        # header.extend(['base_vel_x', 'base_vel_y'])
        # 基座位置
        # header.extend(['base_pos_x', 'base_pos_y', 'base_pos_theta'])
        header.extend(['base_pos_x', 'base_pos_y'])
        
        self.csv_writer.writerow(header)
        rospy.loginfo(f"Data collection started. Saving to: {self.csv_filename}")
        rospy.loginfo(f"Expected {self.num_joints} joints per arm.")

    def joint_state_left_callback(self, msg):
        # if len(msg.position) >= self.num_joints and len(msg.velocity) >= self.num_joints:
        if len(msg.position) >= self.num_joints:
            self.left_joint_state = msg
            self.check_all_data_received()

    def joint_state_right_callback(self, msg):
        # if len(msg.position) >= self.num_joints and len(msg.velocity) >= self.num_joints:
        if len(msg.position) >= self.num_joints:
            self.right_joint_state = msg
        self.check_all_data_received()

    # def base_vel_callback(self, msg):
    #     self.base_vel = msg
    #     self.check_all_data_received()

    def base_pos_callback(self, msg):
        self.base_pos = msg
        self.check_all_data_received()

    def check_all_data_received(self):
        """检查是否所有必需的数据都已收到"""
        if not self.all_data_received:
            # if self.left_joint_state and self.right_joint_state and self.base_vel and self.base_pos:
            if self.left_joint_state and self.right_joint_state and self.base_pos:
                self.all_data_received = True
                rospy.loginfo("All required data sources received. Starting to record data.")

    def check_stop_condition(self):
        # 只有在开始记录数据后才检查停止条件
        if not self.all_data_received:
            return False
            
        # 检查时间是否超过阈值
        if time.time() - self.start_time < self.duration_threshold:
            return False

        # 检查所有关节位置是否接近0
        all_close_to_zero = True
        if self.left_joint_state and self.right_joint_state:
            # 检查左侧所有关节
            for pos in self.left_joint_state.position:
                if abs(pos) > self.joint_zero_threshold:
                    all_close_to_zero = False
                    break
            # 检查右侧所有关节
            if all_close_to_zero: # 只有左侧都接近0时才检查右侧
                for pos in self.right_joint_state.position:
                    if abs(pos) > self.joint_zero_threshold:
                        all_close_to_zero = False
                        break
        else:
            # 如果任一关节状态未收到，不能算作停止
            all_close_to_zero = False

        # 将当前状态记录到队列中
        self.stopped_recently.append(all_close_to_zero)
        
        # 检查队列中是否所有最近的状态都为True（都接近0）
        # 这样可以避免因瞬时抖动而误判停止
        return all(self.stopped_recently)

    def run(self):
        rate = rospy.Rate(self.rate) # 使用参数设置的频率
        while not rospy.is_shutdown():
            # 检查停止条件
            if self.check_stop_condition():
                rospy.loginfo("Stop condition met: Duration exceeded and joints are near zero for a sustained period. Stopping...")
                break

            # 只有在所有数据都收到后才开始记录
            if self.all_data_received:
                # 准备写入的数据行
                row = [time.time()] # 使用当前系统时间作为统一时间戳

                # 处理左侧关节状态 (确保长度足够)
                if self.left_joint_state and len(self.left_joint_state.position) >= self.num_joints and len(self.left_joint_state.velocity) >= self.num_joints:
                # if self.left_joint_state and len(self.left_joint_state.position) >= self.num_joints:
                    row.extend(self.left_joint_state.position[:self.num_joints]) # 取前num_joints个值
                    row.extend(self.left_joint_state.velocity[:self.num_joints])
                else:
                    # 如果数据不足，填充空值
                    row.extend([''] * (self.num_joints * 2))

                # 处理右侧关节状态 (确保长度足够)
                if self.right_joint_state and len(self.right_joint_state.position) >= self.num_joints and len(self.right_joint_state.velocity) >= self.num_joints:
                # if self.right_joint_state and len(self.right_joint_state.position) >= self.num_joints:
                    row.extend(self.right_joint_state.position[:self.num_joints])
                    row.extend(self.right_joint_state.velocity[:self.num_joints])
                else:
                    # 如果数据不足，填充空值
                    row.extend([''] * (self.num_joints * 2))

                # 处理基座速度
                # if self.base_vel:
                #     # row.extend([self.base_vel.x, self.base_vel.y, self.base_vel.theta])
                #     row.extend([self.base_vel.x, self.base_vel.y])
                # else:
                #     # row.extend(['', '', ''])
                #     row.extend(['', ''])

                # 处理基座位置
                if self.base_pos:
                    # row.extend([self.base_pos.x, self.base_pos.y, self.base_pos.theta])
                    row.extend([self.base_pos.x, self.base_pos.y])
                else:
                    # row.extend(['', '', ''])
                    row.extend(['', ''])

                # 写入CSV行
                self.csv_writer.writerow(row)

            rate.sleep()

        # 确保文件被关闭
        self.csv_file.close()
        rospy.loginfo(f"Data collection finished. Data saved to {self.csv_filename}")

if __name__ == '__main__':
    collector = DataCollector()
    collector.run()
#!/usr/bin/env python3
import rospy
import yaml
import numpy as np
from scipy.interpolate import CubicSpline
from sensor_msgs.msg import JointState
from pcl_msgs.srv import UpdateFilename, UpdateFilenameResponse
import os


class ArmTrajectoryPlayer:
    def __init__(self):
        # File directory
        self.file_dir = rospy.get_param('~file_dir', './src/arm_controller/config/episodes')

        # Joint number
        self.joint_num = rospy.get_param('~joint_num', 4)

        # Frequency
        self.freq = rospy.get_param('~freq', 100)

        # Publishers
        self.left_pub = rospy.Publisher('/left/Arm/JointCommand', JointState, queue_size=10)
        self.right_pub = rospy.Publisher('/right/Arm/JointCommand', JointState, queue_size=10)

        # Service
        self.service = rospy.Service('/Arm/Action', UpdateFilename, self.handle_play_trajectory)

        # State
        self.is_playing = False

        rospy.loginfo("ArmTrajectoryPlayer ready. Waiting for update_filename service call...")

    def handle_play_trajectory(self, req):
        if self.is_playing:
            msg = "Already playing a trajectory. Please wait until completion."
            rospy.logwarn(msg)
            return UpdateFilenameResponse(success=False)

        rospy.loginfo(f"Accept request for action [{req.filename}]")
        filename = os.path.join(self.file_dir, req.filename + '.yaml')
        if not os.path.isfile(filename):
            msg = f"YAML file not found: {filename}"
            rospy.logerr(msg)
            return UpdateFilenameResponse(success=False)

        try:
            with open(filename, 'r') as f:
                data = yaml.safe_load(f)
        except Exception as e:
            msg = f"Failed to load YAML file '{filename}': {str(e)}"
            rospy.logerr(msg)
            return UpdateFilenameResponse(success=False)

        if not isinstance(data, list) or len(data) == 0:
            msg = "YAML must contain a non-empty list of trajectory points."
            rospy.logerr(msg)
            return UpdateFilenameResponse(success=False)

        n = len(data)
        # --- 强制检查：首点和末点必须包含 left 和 right ---
        first_pt = data[0]
        last_pt = data[-1]

        if not ('left' in first_pt and 'right' in first_pt):
            msg = "First trajectory point must contain both 'left' and 'right'."
            rospy.logerr(msg)
            return UpdateFilenameResponse(success=False)

        if not ('left' in last_pt and 'right' in last_pt):
            msg = "Last trajectory point must contain both 'left' and 'right'."
            rospy.logerr(msg)
            return UpdateFilenameResponse(success=False)

        # --- 解析所有点，用 last_valid 填充中间缺失 ---
        timestamps = []
        left_positions = []
        right_positions = []

        last_left = None
        last_right = None
        try:
            for i, pt in enumerate(data):
                if 'timestamp' not in pt:
                    raise ValueError(f"Point {i}: missing 'timestamp'")

                ts = float(pt['timestamp'])
                timestamps.append(ts)

                # 处理 left
                if 'left' in pt:
                    left_val = pt['left']
                    if not (isinstance(left_val, (list, tuple)) and len(left_val) == self.joint_num):
                        raise ValueError(f"Point {i}: 'left' must be a list of {self.joint_num} floats")
                    last_left = [float(x) for x in left_val]
                # else: 保留 last_left（但首尾已保证存在，中间缺失合法）

                # 处理 right
                if 'right' in pt:
                    right_val = pt['right']
                    if not (isinstance(right_val, (list, tuple)) and len(right_val) == self.joint_num):
                        raise ValueError(f"Point {i}: 'right' must be a list of {self.joint_num} floats")
                    last_right = [float(x) for x in right_val]
                # else: 保留 last_right

                # 此时 last_left 和 last_right 一定非 None（因为首点已初始化）
                if last_left is None or last_right is None:
                    # 理论上不会发生，因首点已检查
                    raise ValueError(f"Point {i}: missing initial left/right")

                left_positions.append(last_left.copy())
                right_positions.append(last_right.copy())

        except Exception as e:
            msg = f"Trajectory parsing error: {str(e)}"
            rospy.logerr(msg)
            return UpdateFilenameResponse(success=False)

        # 转为 numpy
        timestamps = np.array(timestamps)
        left_positions = np.array(left_positions)
        right_positions = np.array(right_positions)

        # 确保时间单调
        if not np.all(np.diff(timestamps) > 0):
            # 允许相等？不，CubicSpline 要求严格递增，所以先去重
            order = np.argsort(timestamps, kind='mergesort')  # 稳定排序
            timestamps = timestamps[order]
            left_positions = left_positions[order]
            right_positions = right_positions[order]

            # 去除重复时间戳（保留最后一次出现）
            _, unique_idx = np.unique(timestamps, return_index=True)
            timestamps = timestamps[unique_idx]
            left_positions = left_positions[unique_idx]
            right_positions = right_positions[unique_idx]

        if len(timestamps) < 2:
            msg = "Need at least two distinct timestamps for interpolation."
            rospy.logerr(msg)
            return UpdateFilenameResponse(success=False)

        # 构建样条
        try:
            left_splines = CubicSpline(timestamps, left_positions, bc_type='clamped')
            right_splines = CubicSpline(timestamps, right_positions, bc_type='clamped')
        except Exception as e:
            msg = f"Spline construction failed: {str(e)}"
            rospy.logerr(msg)
            return UpdateFilenameResponse(success=False)

        # ===== 播放逻辑（与之前相同）=====
        t_start = timestamps[0]
        t_end = timestamps[-1]
        rospy.loginfo(f"Starting playback from {t_start} to {t_end} ({t_end - t_start:.2f}s)")

        self.is_playing = True
        rate = rospy.Rate(self.freq)
        start_real = rospy.Time.now().to_sec()

        try:
            while not rospy.is_shutdown():
                current_t = t_start + (rospy.Time.now().to_sec() - start_real)
                if current_t > t_end:
                    current_t = t_end

                left_pos = left_splines(current_t).tolist()
                right_pos = right_splines(current_t).tolist()

                now = rospy.Time.now()
                left_msg = JointState()
                right_msg = JointState()
                left_msg.header.stamp = now
                right_msg.header.stamp = now
                left_msg.position = left_pos
                right_msg.position = right_pos
                
                # left_msg = JointState(header=now, name=self.joint_names_left, position=left_pos)
                # right_msg = JointState(header=now, name=self.joint_names_right, position=right_pos)
                self.left_pub.publish(left_msg)
                self.right_pub.publish(right_msg)

                if current_t >= t_end:
                    break
                rate.sleep()

            rospy.loginfo("Playback completed.")
            self.is_playing = False
            return UpdateFilenameResponse(success=True)

        except Exception as e:
            msg = f"Playback runtime error: {str(e)}"
            rospy.logerr(msg)
            self.is_playing = False
            return UpdateFilenameResponse(success=False)
        


if __name__ == '__main__':
    rospy.init_node('arm_trajectory_node', anonymous=False)
    player = ArmTrajectoryPlayer()
    rospy.spin()
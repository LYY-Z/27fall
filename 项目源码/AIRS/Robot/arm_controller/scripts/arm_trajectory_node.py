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

        # Joint number for arms
        self.arm_joint_num = rospy.get_param('~arm_joint_num', 4)
        
        # Joint number for hands
        self.hand_joint_num = rospy.get_param('~hand_joint_num', 6)

        # Frequency
        self.freq = rospy.get_param('~freq', 100)

        # Publishers for arms
        self.left_arm_pub = rospy.Publisher('/left/Arm/JointCommand', JointState, queue_size=10)
        self.right_arm_pub = rospy.Publisher('/right/Arm/JointCommand', JointState, queue_size=10)
        
        # Publishers for hands
        self.left_hand_pub = rospy.Publisher('/cb_left_hand_control_cmd', JointState, queue_size=10)
        self.right_hand_pub = rospy.Publisher('/cb_right_hand_control_cmd', JointState, queue_size=10)

        # Service
        self.service = rospy.Service('/Arm/Action', UpdateFilename, self.handle_play_trajectory)

        # State
        self.is_playing = False

        rospy.loginfo("ArmTrajectoryPlayer ready. Supports both arm and hand trajectories. Waiting for update_filename service call...")

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
        # --- 强制检查：首点和末点必须包含 left_arm 和 right_arm（可选 hand）---
        first_pt = data[0]
        last_pt = data[-1]

        # Check if arms exist in first and last points (at least one of arm/hand should exist)
        arms_exist_in_first = 'left_arm' in first_pt or 'right_arm' in first_pt
        arms_exist_in_last = 'left_arm' in last_pt or 'right_arm' in last_pt
        
        # Check if hands exist in first and last points
        hands_exist_in_first = 'left_hand' in first_pt or 'right_hand' in first_pt
        hands_exist_in_last = 'left_hand' in last_pt or 'right_hand' in last_pt
        
        # At least one type (arm or hand) should exist in both first and last points
        if not (arms_exist_in_first or hands_exist_in_first):
            msg = "First trajectory point must contain at least one of: 'left_arm', 'right_arm', 'left_hand', 'right_hand'."
            rospy.logerr(msg)
            return UpdateFilenameResponse(success=False)
            
        if not (arms_exist_in_last or hands_exist_in_last):
            msg = "Last trajectory point must contain at least one of: 'left_arm', 'right_arm', 'left_hand', 'right_hand'."
            rospy.logerr(msg)
            return UpdateFilenameResponse(success=False)

        # --- 解析所有点，用 last_valid 填充中间缺失 ---
        timestamps = []
        left_arm_positions = []
        right_arm_positions = []
        left_hand_positions = []
        right_hand_positions = []

        # Initialize with None to indicate they don't exist yet
        last_left_arm = None
        last_right_arm = None
        last_left_hand = None
        last_right_hand = None
        
        try:
            for i, pt in enumerate(data):
                if 'timestamp' not in pt:
                    raise ValueError(f"Point {i}: missing 'timestamp'")

                ts = float(pt['timestamp'])
                timestamps.append(ts)

                # 处理 left arm
                if 'left_arm' in pt:
                    left_arm_val = pt['left_arm']
                    if not (isinstance(left_arm_val, (list, tuple)) and len(left_arm_val) == self.arm_joint_num):
                        raise ValueError(f"Point {i}: 'left_arm' must be a list of {self.arm_joint_num} floats")
                    last_left_arm = [float(x) for x in left_arm_val]

                # 处理 right arm
                if 'right_arm' in pt:
                    right_arm_val = pt['right_arm']
                    if not (isinstance(right_arm_val, (list, tuple)) and len(right_arm_val) == self.arm_joint_num):
                        raise ValueError(f"Point {i}: 'right_arm' must be a list of {self.arm_joint_num} floats")
                    last_right_arm = [float(x) for x in right_arm_val]

                # 处理 left hand
                if 'left_hand' in pt:
                    left_hand_val = pt['left_hand']
                    if not (isinstance(left_hand_val, (list, tuple)) and len(left_hand_val) == self.hand_joint_num):
                        raise ValueError(f"Point {i}: 'left_hand' must be a list of {self.hand_joint_num} floats")
                    last_left_hand = [float(x) for x in left_hand_val]

                # 处理 right hand
                if 'right_hand' in pt:
                    right_hand_val = pt['right_hand']
                    if not (isinstance(right_hand_val, (list, tuple)) and len(right_hand_val) == self.hand_joint_num):
                        raise ValueError(f"Point {i}: 'right_hand' must be a list of {self.hand_joint_num} floats")
                    last_right_hand = [float(x) for x in right_hand_val]

                # Append current values (could be None if not updated in this point)
                # For arms
                if last_left_arm is not None:
                    left_arm_positions.append(last_left_arm.copy())
                else:
                    left_arm_positions.append([0.0] * self.arm_joint_num)  # Default values
                    
                if last_right_arm is not None:
                    right_arm_positions.append(last_right_arm.copy())
                else:
                    right_arm_positions.append([0.0] * self.arm_joint_num)  # Default values

                # For hands
                if last_left_hand is not None:
                    left_hand_positions.append(last_left_hand.copy())
                else:
                    left_hand_positions.append([0.0] * self.hand_joint_num)  # Default values
                    
                if last_right_hand is not None:
                    right_hand_positions.append(last_right_hand.copy())
                else:
                    right_hand_positions.append([0.0] * self.hand_joint_num)  # Default values

        except Exception as e:
            msg = f"Trajectory parsing error: {str(e)}"
            rospy.logerr(msg)
            return UpdateFilenameResponse(success=False)

        # 转为 numpy
        timestamps = np.array(timestamps)
        left_arm_positions = np.array(left_arm_positions)
        right_arm_positions = np.array(right_arm_positions)
        left_hand_positions = np.array(left_hand_positions)
        right_hand_positions = np.array(right_hand_positions)

        # 确保时间单调
        if not np.all(np.diff(timestamps) > 0):
            # 允许相等？不，CubicSpline 要求严格递增，所以先去重
            order = np.argsort(timestamps, kind='mergesort')  # 稳定排序
            timestamps = timestamps[order]
            left_arm_positions = left_arm_positions[order]
            right_arm_positions = right_arm_positions[order]
            left_hand_positions = left_hand_positions[order]
            right_hand_positions = right_hand_positions[order]

            # 去除重复时间戳（保留最后一次出现）
            _, unique_idx = np.unique(timestamps, return_index=True)
            timestamps = timestamps[unique_idx]
            left_arm_positions = left_arm_positions[unique_idx]
            right_arm_positions = right_arm_positions[unique_idx]
            left_hand_positions = left_hand_positions[unique_idx]
            right_hand_positions = right_hand_positions[unique_idx]

        if len(timestamps) < 2:
            msg = "Need at least two distinct timestamps for interpolation."
            rospy.logerr(msg)
            return UpdateFilenameResponse(success=False)

        # 构建样条 - 分别为臂和手创建
        try:
            # Arms
            if left_arm_positions.shape[1] > 0 and np.any(left_arm_positions):  # Check if left positions exist and are not all zeros
                left_arm_splines = CubicSpline(timestamps, left_arm_positions, bc_type='clamped')
            else:
                left_arm_splines = None
                
            if right_arm_positions.shape[1] > 0 and np.any(right_arm_positions):
                right_arm_splines = CubicSpline(timestamps, right_arm_positions, bc_type='clamped')
            else:
                right_arm_splines = None
            
            # Hands
            if left_hand_positions.shape[1] > 0 and np.any(left_hand_positions):
                left_hand_splines = CubicSpline(timestamps, left_hand_positions, bc_type='clamped')
            else:
                left_hand_splines = None
                
            if right_hand_positions.shape[1] > 0 and np.any(right_hand_positions):
                right_hand_splines = CubicSpline(timestamps, right_hand_positions, bc_type='clamped')
            else:
                right_hand_splines = None

        except Exception as e:
            msg = f"Spline construction failed: {str(e)}"
            rospy.logerr(msg)
            return UpdateFilenameResponse(success=False)

        # ===== 播放逻辑 =====
        t_start = timestamps[0]
        t_end = timestamps[-1]
        rospy.loginfo(f"Starting playback from {t_start} to {t_end} ({t_end - t_start:.2f}s)")
        rospy.loginfo(f"Playing: Arm={any([left_arm_splines, right_arm_splines])}, Hand={any([left_hand_splines, right_hand_splines])}")

        self.is_playing = True
        rate = rospy.Rate(self.freq)
        start_real = rospy.Time.now().to_sec()

        try:
            while not rospy.is_shutdown():
                current_t = t_start + (rospy.Time.now().to_sec() - start_real)
                if current_t > t_end:
                    current_t = t_end

                # Get interpolated positions
                # Arms
                left_arm_pos = left_arm_splines(current_t).tolist() if left_arm_splines else None
                right_arm_pos = right_arm_splines(current_t).tolist() if right_arm_splines else None
                
                # Hands
                left_hand_pos = left_hand_splines(current_t).tolist() if left_hand_splines else None
                right_hand_pos = right_hand_splines(current_t).tolist() if right_hand_splines else None

                now = rospy.Time.now()
                
                # Publish arm commands if they exist
                if left_arm_pos is not None:
                    left_arm_msg = JointState()
                    left_arm_msg.header.stamp = now
                    left_arm_msg.position = left_arm_pos
                    self.left_arm_pub.publish(left_arm_msg)
                    
                if right_arm_pos is not None:
                    right_arm_msg = JointState()
                    right_arm_msg.header.stamp = now
                    right_arm_msg.position = right_arm_pos
                    self.right_arm_pub.publish(right_arm_msg)
                
                # Publish hand commands if they exist
                if left_hand_pos is not None:
                    left_hand_msg = JointState()
                    left_hand_msg.header.stamp = now
                    left_hand_msg.position = left_hand_pos
                    self.left_hand_pub.publish(left_hand_msg)
                    
                if right_hand_pos is not None:
                    right_hand_msg = JointState()
                    right_hand_msg.header.stamp = now
                    right_hand_msg.position = right_hand_pos
                    self.right_hand_pub.publish(right_hand_msg)

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
#!/usr/bin/env python3
import rospy
import numpy as np
import signal
import sys
import threading
import yaml
import time
from sensor_msgs.msg import JointState
from scipy.interpolate import CubicSpline


PRIMES = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97]


class DualArmTraversal:
    def __init__(self):
        rospy.init_node('dual_arm_traversal', anonymous=True)
        
        # 从参数服务器获取YAML配置文件路径
        config_path = rospy.get_param('~config_path', None)
        if config_path:
            # 从YAML文件加载配置
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            # 解析关节限位 (一维数组格式: [min1, max1, min2, max2, ...])
            raw_limits = config['traversal']['joint_limits']
        else:
            # 从参数服务器直接获取 (兼容旧格式)
            raise RuntimeError("Parameter 'config_path' is required.")
        
        # 从参数服务器获取关节数量
        self.joint_num = rospy.get_param('~arm_joint_num', 4)
        self.traversal_joint_num = rospy.get_param('~traversal_arm_joint_num', 3)
        
        # 速度限制 (rad/s)
        self.max_speed = rospy.get_param('~max_speed', 0.3)  # 默认速度约18度/秒
        
        # 采样点数 (可调整)
        self.num_samples = rospy.get_param('~num_samples', 200)

        if len(raw_limits) != self.traversal_joint_num * 4:  # self.traversal_joint_num 个关节 * 2 (min, max)
            rospy.logerr(f"Require exactly {self.traversal_joint_num} values for joint limits: [j1_min, j1_max, j2_min, j2_max, j3_min, j3_max, ...]")
            sys.exit(1)
        
        # 重构为 self.traversal_joint_num * 2 对(min, max)
        self.joint_limits = [(raw_limits[i], raw_limits[i+1]) for i in range(0, self.traversal_joint_num * 4, 2)]
        
        # 验证关节限位
        for i, (min_val, max_val) in enumerate(self.joint_limits):
            if min_val >= max_val:
                rospy.logerr(f"Invalid limits for joint {i}: min({min_val}) >= max({max_val})")
                sys.exit(1)
        
        # 运动控制频率 (Hz)
        self.control_freq = 100
        self.rate = rospy.Rate(self.control_freq)
        
        # ROS发布者
        self.left_pub = rospy.Publisher('/left/Arm/JointCommand', JointState, queue_size=10)
        self.right_pub = rospy.Publisher('/right/Arm/JointCommand', JointState, queue_size=10)
        
        # 状态变量
        self.current_position = np.zeros(self.traversal_joint_num * 2)
        self.target_position = None
        self.moving = False
        self.shutdown_flag = False
        
        # 生成遍历路径 (包含起始和结束点)
        self.path = self.generate_halton_path_with_start_end()
        
        # 设置信号处理器
        signal.signal(signal.SIGINT, self.signal_handler)
        rospy.on_shutdown(self.cleanup)

    def halton_sequence(self, n, dim):
        """生成dim维Halton序列"""
        primes = PRIMES[:dim]  # 前dim个质数
        sequence = np.zeros((n, dim))
        
        for d in range(dim):
            base = primes[d]
            idx = np.arange(1, n + 1)
            f = 1.0 / base
            while np.any(idx > 0):
                sequence[:, d] += f * (idx % base)
                idx //= base
                f /= base

        # 添加循环移位随机性
        shift = np.random.randint(0, n)
        sequence = np.roll(sequence, shift, axis=0)

        return sequence

    def generate_halton_path_with_start_end(self):
        """生成包含起始和结束点的遍历路径"""
        rospy.loginfo("Generating Halton sequence path with start/end interpolation...")
        
        # 起始点 (所有关节为0)
        start_point = np.zeros(2*self.traversal_joint_num)
        
        # 生成遍历点
        points = self.halton_sequence(self.num_samples, 2*self.traversal_joint_num)
        
        # 映射到实际关节范围
        for i in range(2*self.traversal_joint_num):
            min_val, max_val = self.joint_limits[i]
            points[:, i] = min_val + points[:, i] * (max_val - min_val)
        
        # 贪心路径规划 (TSP近似)
        path = []
        current = start_point.copy()
        remaining = points.copy()
        
        # 随机选择第一个点
        if len(remaining) > 0:
            first_idx = np.random.randint(0, len(remaining))
            first_point = remaining[first_idx]
            path.append(first_point)
            current = first_point
            remaining = np.delete(remaining, first_idx, axis=0)
        
        # 继续贪心选择剩余点
        while len(remaining) > 0:
            # 计算到所有剩余点的欧氏距离
            dists = np.linalg.norm(remaining - current, axis=1)
            idx = np.argmin(dists)  # 选择最近点
            next_point = remaining[idx]
            path.append(next_point)
            current = next_point
            remaining = np.delete(remaining, idx, axis=0)
        
        # 添加结束点 (回到起始点)
        path.append(start_point)
        
        rospy.loginfo(f"Path generated with {len(path)-1} waypoints")
        return np.array(path)

    def move_to_position(self, target):
        """使用三次样条插值平滑移动到目标位置"""
        if self.shutdown_flag:
            return
        
        delta = target - self.current_position
        max_delta = np.max(np.abs(delta))
        
        # 计算所需时间 (保证速度不超过限制)
        duration = max_delta / self.max_speed if max_delta > 1e-5 else 0.01
        
        # 定义时间点 (稀疏)
        times = np.array([0, duration])
        jnt_points = np.array([self.current_position, target])
        
        # 创建三次样条插值函数
        interp_func = CubicSpline(times, jnt_points)
        
        # 定义稠密时间序列
        waytimes = np.linspace(0, duration, max(2, int(duration * self.control_freq)))
        
        # 执行插值轨迹
        self.moving = True
        for t in waytimes:
            if self.shutdown_flag:
                break
            
            pos = interp_func(t)
            
            # 检查关节限位
            for i in range(2*self.traversal_joint_num):
                min_val, max_val = self.joint_limits[i]
                pos[i] = max(min_val, min(max_val, pos[i]))
            
            # 分离左右臂位置
            left_pos = pos[0: self.traversal_joint_num]
            right_pos = pos[self.traversal_joint_num: 2*self.traversal_joint_num]

            delta_joint_num = self.joint_num - self.traversal_joint_num
            if delta_joint_num > 0:
                left_pos = np.pad(left_pos, (0, delta_joint_num), constant_values=0.0)
                right_pos = np.pad(right_pos, (0, delta_joint_num), constant_values=0.0)

            # 创建并发布JointState消息
            left_msg = JointState()
            left_msg.header.stamp = rospy.Time.now()
            # left_msg.name = self.left_joint_names
            left_msg.position = left_pos.tolist()
            
            right_msg = JointState()
            right_msg.header.stamp = rospy.Time.now()
            # right_msg.name = self.right_joint_names
            right_msg.position = right_pos.tolist()
            
            self.left_pub.publish(left_msg)
            self.right_pub.publish(right_msg)
            
            self.current_position = pos.copy()
            self.rate.sleep()
        
        self.moving = False

    def run(self):
        """主执行循环"""
        rospy.loginfo("Starting dual-arm traversal...")
        start_time = rospy.Time.now()
        
        try:
            # 先移动到路径第一个点（从零点开始）
            rospy.loginfo("Moving to initial position...")
            # 直接设置初始位置为零点
            self.current_position = np.zeros(self.traversal_joint_num * 2)
            self.move_to_position(self.path[0])
            
            # 遍历路径
            start_time = time.time()
            for i in range(1, len(self.path)):
                if self.shutdown_flag:
                    break
                
                step_start_time = time.time()
                self.move_to_position(self.path[i])

                time.sleep(2.0)  # 每个点停留2秒以采集静态效果
                
                step_duration = time.time() - step_start_time
                total_duration = time.time() - start_time
                avg_duration_per_step = total_duration / i if i > 0 else 0
                remaining_steps = len(self.path) - 1 - i
                remaining_time = avg_duration_per_step * remaining_steps
                
                rospy.loginfo(
                    f"Waypoint[{i}/{len(self.path)-1}] "
                    f"Step time: {step_duration:.2f}s, "
                    f"Total time: {total_duration/60:.2f}min, "
                    f"Estimated remaining: {remaining_time/60:.2f}min"
                )
                
        finally:
            elapsed = time.time() - start_time
            rospy.loginfo(f"Traversal completed in {elapsed:.2f} seconds. Shutting down...")
            self.cleanup()

    def cleanup(self):
        """清理资源"""
        self.shutdown_flag = True
        rospy.loginfo("Stopping arm movements...")
        
        # 发送停止命令
        stop_msg = JointState()
        stop_msg.header.stamp = rospy.Time.now()
        # stop_msg.name = self.left_joint_names + self.right_joint_names
        stop_msg.position = [0.0] * (self.joint_num * 2)
        
        for _ in range(5):  # 确保命令送达
            self.left_pub.publish(stop_msg)
            self.right_pub.publish(stop_msg)
            rospy.sleep(0.1)
        
        rospy.loginfo("Cleanup complete")

    def signal_handler(self, sig, frame):
        """处理Ctrl+C中断"""
        rospy.loginfo("Interrupt received! Stopping traversal...")
        self.shutdown_flag = True

if __name__ == '__main__':
    try:
        node = DualArmTraversal()
        threading.Thread(target=node.run, daemon=True).start()
        rospy.spin()
    except rospy.ROSInterruptException:
        pass
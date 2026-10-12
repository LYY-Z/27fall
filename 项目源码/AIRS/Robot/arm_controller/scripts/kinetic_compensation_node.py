#!/usr/bin/env python3
import sys
import rospy
import numpy as np
import pinocchio as pin
from sensor_msgs.msg import JointState
from geometry_msgs.msg import Pose2D
from typing import Optional, Dict


class CompensationNode:
    """双臂推理ROS节点"""
    def __init__(self):        
        # 初始化ROS节点
        rospy.init_node('kinetic_compensation_node', anonymous=True)

        # 覆盖模型保存配置
        self.model_path = rospy.get_param('~model_path', '../mujoco_rl_env/ballbotgym/assets/uni.urdf')

        # 推理频率，默认100Hz
        self.freq = float(rospy.get_param('~freq', 100))
        self.rate = rospy.Rate(self.freq)

        # 关节数量
        self.joint_num = rospy.get_param('~arm_joint_num', 4)  # 默认4个关节
        
        # 是否包含速度
        self.has_velocity = rospy.get_param('~has_velocity', True)
        
        # 缓存关节状态
        self.left_joint_state: Optional[JointState] = None
        self.right_joint_state: Optional[JointState] = None
        
        # 订阅关节状态
        rospy.Subscriber('/left/Arm/JointState', JointState, self._left_joint_callback)
        rospy.Subscriber('/right/Arm/JointState', JointState, self._right_joint_callback)
        
        # 发布补偿量
        self.com_pos_pub = rospy.Publisher('/com_pos', Pose2D, queue_size=10)
        self.com_vel_pub = rospy.Publisher('/com_vel', Pose2D, queue_size=10)
        
        # 状态同步标志
        self.pin_model = pin.buildModelFromUrdf(self.model_path)
        self.pin_data = self.pin_model.createData()
        self.pin_q = np.zeros(self.pin_model.nq)
        self.pin_dq = np.zeros(self.pin_model.nv)

        left_arm_joint_names = [f"left_arm_joint_{i+1}" for i in range(self.joint_num)]
        right_arm_joint_names = [f"right_arm_joint_{i+1}" for i in range(self.joint_num)]

        self.left_arm_pin_indices = self.get_joint_indices_from_names(left_arm_joint_names)
        self.right_arm_pin_indices = self.get_joint_indices_from_names(right_arm_joint_names)
        
        rospy.loginfo("Arm Inference Node initialized")
    
    
    def get_joint_indices_from_names(self, joint_names):
        indices = []
        for name in joint_names:
            if name in self.pin_model.names:
                joint_id = self.pin_model.getJointId(name)
                # 获取这个关节在q向量中的起始位置
                idx_q = self.pin_model.joints[joint_id].idx_q
                indices.append(idx_q)
        return indices
    
    def _left_joint_callback(self, msg: JointState):
        """左臂关节状态回调"""
        if not self.has_velocity:
            # 手动差分计算速度
            dt = msg.header.stamp.to_sec() - self.left_joint_state.header.stamp.to_sec()
            for pos, last_pos in zip(msg.position, self.left_joint_state.position):
                msg.velocity = (pos - last_pos) / dt

        self.left_joint_state = msg

    def _right_joint_callback(self, msg: JointState):
        """右臂关节状态回调"""
        if not self.has_velocity:
            # 手动差分计算速度
            dt = msg.header.stamp.to_sec() - self.right_joint_state.header.stamp.to_sec()
            for pos, last_pos in zip(msg.position, self.right_joint_state.position):
                msg.velocity = (pos - last_pos) / dt

        self.right_joint_state = msg
    
    def run(self):
        """运行节点"""        
        rospy.loginfo("Arm Compensation Node started running")
        while not rospy.is_shutdown():
            if self.left_joint_state is not None and self.right_joint_state is not None:
                # 更新Pinocchio模型状态
                self.pin_q[self.left_arm_pin_indices] = self.left_joint_state.position
                self.pin_q[self.right_arm_pin_indices] = self.right_joint_state.position
                self.pin_dq[self.left_arm_pin_indices] = self.left_joint_state.velocity
                self.pin_dq[self.right_arm_pin_indices] = self.right_joint_state.velocity

                # 计算质心位置和速度
                pin.centerOfMass(self.pin_model, self.pin_data, self.pin_q, self.pin_dq)

                # 发布质心位置
                com_pos_msg = Pose2D()
                com_pos_msg.x = self.pin_data.com[0][0]
                com_pos_msg.y = self.pin_data.com[0][1]
                self.com_pos_pub.publish(com_pos_msg)
                
                # 发布质心速度
                com_vel_msg = Pose2D()
                com_vel_msg.x = self.pin_data.vcom[0][0]
                com_vel_msg.y = self.pin_data.vcom[0][1]
                self.com_vel_pub.publish(com_vel_msg)
            
            self.rate.sleep()


def main():
    """主函数"""    
    try:
        node = CompensationNode()
        node.run()
    except rospy.ROSInterruptException:
        rospy.loginfo("Compensation Node terminated")
    # except Exception as e:
    #     rospy.logerr(f"Error in Compensation Node: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
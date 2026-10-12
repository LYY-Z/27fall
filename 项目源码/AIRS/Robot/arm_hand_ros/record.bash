#!/bin/bash


source /home/nvidia/work/arm_hand_ros/devel/setup.bash

nohup  rosbag play arm_data.bag /right/Arm/JointState:=/right/Arm/JointCommand /left/Arm/JointState:=/left/Arm/JointCommand
 >/dev/null 2>&1 &
nohup  rosbag record -O all_data /left/Arm/JointCommand /right/Arm/JointCommand /cb_left_hand_control_cmd /cb_right_hand_control_cmd
 >/dev/null 2>&1 &

#!/bin/bash

sudo ip link set can0 down
sudo ip link set can0 up type can bitrate 1000000

source /home/nvidia/work/arm_hand_ros/devel/setup.bash

nohup roslaunch taihu_motor dual_forearm.launch >/dev/null 2>&1 &
nohup roslaunch linker_hand_sdk_ros linker_hand_double.launch >/dev/null 2>&1 &

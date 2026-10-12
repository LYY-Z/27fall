# 1. 启动环境
此处仅给出示例，具体参考相应包中的说明，注意真机和仿真是 **二选一** 的
## 1.1 真机
需要 [`package_name`](http://10.60.170.3:30080/ballwheelrobot/package_name) 位于工作空间中
路径：`"~/work/arm_hand_ros"`
### 1.1.1 启动手臂钛虎电机发布-订阅节点
```shell
sudo ip link set can0 up type can bitrate 1000000
roslaunch taihu_motor dual_forearm.launch
```
### 1.1.2 启动灵心巧手发布-订阅节点
```shell
conda deactivate
roslaunch linker_hand_sdk_ros linker_hand_double.launch
```

## 1.2 仿真
需要 [`mujoco_rl_env`](http://10.60.170.3:30080/ballwheelrobot/mujoco_rl_env) 包位于工作空间中
```shell
roslaunch mujoco_rl_env robot.launch
```

## 1.3 测试机器人发布信息成功
显示机器人底盘轮子关节状态信息（`sensor_msgs/JointState`）：
```shell
rostopic echo /chassis_states_topic
```
显示机器人 IMU 状态信息（`sensor_msgs/Imu`）：
```shell
rostopic echo /imu/data
```

# 2. 启动控制器
给权限（初次使用）
```shell
sudo chmod a+rx src/arm_controller/scripts/*.py
```

遍历手臂空间，收集数据
```shell
roslaunch arm_controller traversal_arm_and_collect_data.launch
```

做一个预设的动作
```shell
rosservice call /Arm/Action "filename: 'front_raise4'"
```



journalctl -u roslaunch.service -n 500 --no-pager

蓝牙启动
```
bluetoothctl
```

蓝牙扫描设备
```
scan on
scan off
```

蓝牙配对
```
pair XX:XX:XX:XX:XX:XX
remove XX:XX:XX:XX:XX:XX
paired-devices
```

蓝牙连接
```
connect XX:XX:XX:XX:XX:XX
disconnect XX:XX:XX:XX:XX:XX
devices
```
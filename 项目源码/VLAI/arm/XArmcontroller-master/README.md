# XArmController

基于达妙电机 MIT 协议的 xArm 七自由度机械臂控制库，通过 SocketCAN（can0/can1）接口驱动电机。

---

## 文件说明

### XArmcontroller.py

底层电机控制模块，适用于单路或双路 CAN 总线。

**主要功能：**
- 支持 DM4310 / DM4340 / DM8006 / DM8009 / DM6006 等型号电机
- 内置 xArm 七自由度标准配置 `ARM_7DOF_LIMITS`
- 提供使能、失能、MIT 控制、力矩控制、位置读取等接口

**基本用法：**

```python
from XArmcontroller import XArmController, ARM_7DOF_LIMITS, MITParam

ctrl = XArmController({
    "can0": ARM_7DOF_LIMITS,   # 右臂
    "can1": ARM_7DOF_LIMITS,   # 左臂
})

ctrl.enable_all()

# 读取关节状态
positions   = ctrl.get_positions("can0")
velocities  = ctrl.get_velocities("can0")

# 力矩控制
ctrl.torque_control_all("can0", [0.0] * 7)

# MIT 控制（位置+速度+力矩）
params = [MITParam(kp=50.0, kd=1.2, q=0.0, dq=0.0, tau=0.0)] * 7
ctrl.mit_control_all("can0", params)

ctrl.recv_all()
ctrl.disable_all()
ctrl.close()
```

---

### XArmcontroller_v2.py

在 v1 基础上增加了双臂统一管理、夹爪控制和轨迹插值功能。

**主要新增功能：**
- 双臂统一管理，通过 `side="left"` / `side="right"` / `side=None` 选择操作对象
- 七轴插值位置控制（minimum-jerk 或 linear 轨迹）
- 夹爪独立控制（`gripper_control`）
- 线程并行双臂运动（`_run_parallel`）

**基本用法：**

```python
from XArmcontroller_v2 import XArmController

ctrl = XArmController(right_can="can0", left_can="can1")
ctrl.enable()

# 插值运动到目标关节角（minimum-jerk，耗时 3 秒）
target = [0.0, 0.3, 0.0, -0.5, 0.0, 0.5, 0.0]
ctrl.arm_control(target, duration=3.0, side="right")

# 夹爪控制（0=夹紧，-1=张开）
ctrl.gripper_control(0.0, duration=1.5, side="right")

# 读取状态
states = ctrl.get_arm_states(side="right")

ctrl.disable()
ctrl.close()
```

---

## 上层控制脚本

以下两个脚本均依赖 `XArmcontroller.py` 中的 `XArmController`、`MITParam`、`ARM_7DOF_LIMITS` 等核心接口实现实时力矩控制。

### imdepence_control.py

基于笛卡尔空间阻抗控制的末端力控脚本。

- 利用 Pinocchio 计算正运动学、雅可比矩阵与重力补偿力矩
- 在末端位置和姿态上施加弹簧-阻尼力，转换为关节力矩后通过 MIT 协议下发
- 适用于柔顺接触、力引导等任务

**基本用法：**

```python
# 直接运行，默认连接 can0
python imdepence_control.py
```

### nullspace_control.py

基于任务空间 + 零空间的双臂冗余控制脚本。

- 主任务：末端位置/姿态阻抗控制（加权伪逆雅可比）
- 零空间：关节阻尼，避免冗余关节漂移
- 支持奇异值自适应增益，接近奇异点时自动降低刚度
- 同时控制左臂（can1）和右臂（can0）

**基本用法：**

```python
# 直接运行，默认连接 can0（右臂）和 can1（左臂）
python nullspace_control.py
```

---

## 依赖

```
python-can
numpy
scipy
pinocchio
```

## 硬件要求

- PEAK PCAN-USB Pro FD 或兼容 SocketCAN 的 CAN 适配器
- xArm 七自由度机械臂（达妙电机版本）

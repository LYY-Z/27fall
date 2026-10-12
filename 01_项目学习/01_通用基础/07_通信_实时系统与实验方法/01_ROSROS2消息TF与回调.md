# 01 ROSROS2消息TF与回调

先修：[计算机系统](../02_编程_算法与计算机系统/README.md)。项目：P1—P7。目标：明确接口、时效、恢复和可追溯实验记录。

## 1. 节点、话题和消息怎样组成系统

节点是运行某项功能的进程/执行单元，话题是发布订阅数据通道，消息定义字段和类型。IMU节点发布读数，估计节点订阅读数输出状态，控制节点订阅状态输出命令。话题名一致还不够，类型、单位、frame和时效也必须一致。

service适合请求响应，action适合带进度/取消的较长任务。ROS1与ROS2的通信/执行和包工具不同，不能把roslaunch与ros2 launch命令混用，具体按原项目版本。原始P1、P5、P2目录可能并存不同版本。

## 2. 一个回调并非一个控制周期

订阅回调接收数据，可以更新缓存；定时控制器用一致状态快照计算。每来一条就做完整控制会让控制频率受消息到达影响。多线程执行器回调可能并发，callback group/锁策略需按实现检查。

手算IMU200Hz、视觉10Hz，若控制50Hz，每20ms要运行一次。视觉每100ms更新，控制约5轮用同一帧；需知道帧年龄，不能把重复使用当新观测。两传感时钟不同要先对齐。

## 3. TF是变换关系与时间

map→odom→base→sensor关系应有明确发布者。查询t时刻变换需要对应历史数据，不能把当前姿态用于旧图像而不解释延迟。静态外参与动态位姿不同。

手算laser在base前.2m，激光点laser=[1,0]，base点[1.2,0]；base在map=[2,1]且yaw90°，地图点[2,2.2]。先laser→base再base→map，逆序结果不同。

## 4. 项目与失败

P2末端目标到求解、P5cmd_vel到驱动、P1补偿数据到PID，需追真实callback/topic。实验[综合闭环](../../03_代码实验/03_综合闭环/README.md)仅用Python无ROS，先理解接口再安装系统。

失败：消息类型不匹配；两个TF发布同一边；用最新变换改旧观测；回调阻塞使反馈积压；QoS不兼容丢消息。排错分“数据有没有→内容对不对→时间对不对→控制有没有发布”。

## 5. 英文与练习

“ROS organizes data exchange, but the application still needs explicit message, frame and timing contracts. A subscription callback is not automatically a deterministic control cycle.”

追问：Why can two valid messages be incompatible? They may refer to different times, frames or units.

1. 概念：topic名一样保证连接吗？答：还需类型/通信策略等匹配。
2. 计算：100ms视觉帧供20ms环几轮？答：约5轮，仍同一观测。
3. 代码：旧图像取哪个TF？答：图像采样时刻的变换或明确补偿模型。
4. 解释：控制频率抖动？答：查回调、执行器、锁、消息积压和定时方式。

下一章：[02_CANFDCAN协议与电机反馈](02_CANFDCAN协议与电机反馈.md)。

## 精读补充：把中间步骤讲清楚

### A. “收到消息”和“控制使用”分两个时刻

传感器t=.100采样，.110到回调，控制.120读取。通信延迟10ms、读取时年龄20ms；回调最新也不等于测量当前。若视觉慢100ms、IMU快5ms，快照中各字段必须带各自时间，或由估计器预测对齐后输出统一时间状态。

TF查询要按测量时间；激光安装偏移属于静态外参，机身运动属于动态变换。P1处理后的IMU未复制Header字段，不能仅靠该消息的默认时间戳认为它新鲜。

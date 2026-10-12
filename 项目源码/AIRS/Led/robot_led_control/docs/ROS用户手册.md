# 机器人LED灯带控制系统 - ROS用户手册

本系统通过ROS话题控制机器人4个部位的LED灯带（胸口、左臂、右臂、底盘）。

---

## 1. 系统部署

### 1.1 硬件连接

1. 将STM32板通过USB转TTL连接到上位机
2. 确认串口设备名（通常为`/dev/ttyUSB0`或`/dev/ttyACM0`）
```bash
ls /dev/ttyUSB*
# 或
dmesg | grep tty
```

3. 添加串口权限
```bash
sudo chmod 666 /dev/ttyUSB0
# 或永久添加用户到dialout组
sudo usermod -a -G dialout $USER
# 注销重新登录后生效
```

### 1.2 ROS包安装

```bash
# 进入工作空间
cd ~/catkin_ws/src

# 复制LED控制包
cp -r /path/to/robot_led_control ./

# 编译
cd ~/catkin_ws
catkin_make

# 刷新环境
source devel/setup.bash
```

### 1.3 配置参数

编辑配置文件：`config/led_control.yaml`

```yaml
port: "/dev/ttyUSB0"    # 修改为实际串口设备
baud: 115200            # 波特率（勿改）
sync_arms: true         # 左臂控制右臂同步（推荐开启）
```

### 1.4 启动节点

```bash
# 启动LED驱动节点
roslaunch robot_led_control led_control.launch
```

**正常输出**：

```
[ INFO] Connected to serial port: /dev/ttyUSB0
[ INFO] LED Driver Node Started
[ INFO] LED Driver Node is running...
```

---

## 2. 控制接口

### 2.1 话题说明

**话题名称**：`/robot_led/command`  
**消息类型**：`std_msgs/String`（JSON格式）

### 2.2 控制区域

| 区域名称 | 说明 | LED数量 |
|----------|------|---------|
| `chest` | 胸口 | 24 |
| `left_arm` | 左臂 | 11 |
| `right_arm` | 右臂 | 11 |
| `chassis` | 底盘 | 24 |
| `all` | 所有区域 | 70 |

---

## 3. 使用方法

### 3.1 预设效果（默认白色）

**效果类型**：
- `off` - 关闭
- `solid` - 常亮
- `breathing` - 呼吸灯
- `flowing` - 流水灯
- `marquee` - 跑马灯
- `rainbow` - 彩虹渐变

**命令格式**：
```json
{
    "region": "区域名称",
    "effect": "效果名称",
    "speed": 50
}
```

**参数说明**：
- `speed`: 速度参数（0-100），可选，默认50

**示例1：设置胸口呼吸灯（速度50）**
```bash
rostopic pub /robot_led/command std_msgs/String "data: '{\"region\":\"chest\",\"effect\":\"breathing\",\"speed\":50}'"
```

**示例2：关闭所有LED**

```bash
rostopic pub /robot_led/command std_msgs/String \
  "data: '{\"region\":\"all\",\"effect\":\"off\"}'"
```

**示例3：底盘彩虹效果（速度80）**
```bash
rostopic pub /robot_led/command std_msgs/String \
  "data: '{\"region\":\"chassis\",\"effect\":\"rainbow\",\"speed\":80}'"
```

### 3.2 预设效果（指定颜色）

**命令格式**：
```json
{
    "region": "区域名称",
    "effect": "效果名称",
    "speed": 50,
    "color": [R, G, B]
}
```

**参数说明**：

- `speed`: 速度参数（0-100），可选，默认50

- `color`: RGB颜色数组，范围0-255

**示例1：左臂红色呼吸灯**

```bash
rostopic pub /robot_led/command std_msgs/String \
  "data: '{\"region\":\"left_arm\",\"effect\":\"breathing\",\"speed\":30,\"color\":[255,0,0]}'"
```

**示例2：底盘绿色流水灯**

```bash
rostopic pub /robot_led/command std_msgs/String \
  "data: '{\"region\":\"chassis\",\"effect\":\"flowing\",\"speed\":70,\"color\":[0,255,0]}'"
```

**示例3：胸口蓝色跑马灯**
```bash
rostopic pub /robot_led/command std_msgs/String \
  "data: '{\"region\":\"chest\",\"effect\":\"marquee\",\"speed\":60,\"color\":[0,0,255]}'"
```

### 3.3 自定义颜色数组

**命令格式**：
```json
{
    "region": "区域名称",
    "effect": "custom",
    "start_index": 0,
    "rgb_data": [R,G,B, R,G,B, ...]
}
```

**参数说明**：
- `start_index`: 起始LED索引（0开始）
- `rgb_data`: RGB数组，每3个值表示一个LED

**示例1：设置胸口前3个LED为红、绿、蓝**
```bash
rostopic pub /robot_led/command std_msgs/String \
  "data: '{\"region\":\"chest\",\"effect\":\"custom\",\"start_index\":0,\"rgb_data\":[255,0,0,0,255,0,0,0,255]}'"
```

**示例2：设置底盘5-9号LED为橙色**

```bash
rostopic pub /robot_led/command std_msgs/String \
  "data: '{\"region\":\"chassis\",\"effect\":\"custom\",\"start_index\":5,\"rgb_data\":[255,128,0,255,128,0,255,128,0,255,128,0,255,128,0]}'"
```

---

## 4. Python编程示例

### 4.1 基础控制

```python
#!/usr/bin/env python3
import rospy
from std_msgs.msg import String
import json

def main():
    rospy.init_node('led_controller')
    pub = rospy.Publisher('/robot_led/command', String, queue_size=10)
    rospy.sleep(1.0)  # 等待发布器建立连接
    
    # 示例1：胸口红色呼吸灯
    cmd = {
        "region": "chest",
        "effect": "breathing",
        "speed": 50,
        "color": [255, 0, 0]
    }
    pub.publish(String(data=json.dumps(cmd)))
    
    rospy.sleep(3.0)
    
    # 示例2：底盘彩虹效果
    cmd = {
        "region": "chassis",
        "effect": "rainbow",
        "speed": 60
    }
    pub.publish(String(data=json.dumps(cmd)))
    
    rospy.sleep(3.0)
    
    # 示例3：关闭所有LED
    cmd = {"region": "all", "effect": "off"}
    pub.publish(String(data=json.dumps(cmd)))

if __name__ == '__main__':
    main()
```

---

## 5. 常用场景

### 5.1 待机状态

```python
# 所有区域蓝色呼吸灯（慢速）
cmd = {
    "region": "all",
    "effect": "breathing",
    "speed": 20,
    "color": [0, 100, 255]
}
```

### 5.2 运动状态

```python
# 底盘绿色流水灯（快速）
cmd = {
    "region": "chassis",
    "effect": "flowing",
    "speed": 80,
    "color": [0, 255, 0]
}
```

### 5.3 警告状态

```python
# 胸口红色跑马灯（中速）
cmd = {
    "region": "chest",
    "effect": "marquee",
    "speed": 60,
    "color": [255, 0, 0]
}
```

### 5.4 充电状态

```python
# 底盘黄色呼吸灯（慢速）
cmd = {
    "region": "chassis",
    "effect": "breathing",
    "speed": 25,
    "color": [255, 200, 0]
}
```

### 5.5 庆祝模式

```python
# 全身彩虹效果（快速）
cmd = {
    "region": "all",
    "effect": "rainbow",
    "speed": 90
}
```

---

## 6. 参数调优指南

### 6.1 速度参数

| 速度值 | 效果 | 适用场景 |
|--------|------|----------|
| 0-20 | 极慢 | 待机、充电 |
| 20-40 | 慢 | 呼吸灯、环境光 |
| 40-60 | 中速 | 常规效果 |
| 60-80 | 快 | 运动、警告 |
| 80-100 | 极快 | 紧急、庆祝 |

### 6.2 常用颜色

```python
# 红色系
RED = [255, 0, 0]
ORANGE = [255, 128, 0]
PINK = [255, 100, 150]

# 绿色系
GREEN = [0, 255, 0]
LIME = [150, 255, 0]
CYAN = [0, 255, 150]

# 蓝色系
BLUE = [0, 0, 255]
SKY_BLUE = [0, 150, 255]
PURPLE = [128, 0, 255]

# 白色系
WHITE = [255, 255, 255]
WARM_WHITE = [255, 200, 150]
COOL_WHITE = [200, 220, 255]

# 其他
YELLOW = [255, 255, 0]
```

---

## 7. 手臂同步功能

### 7.1 默认行为

当`sync_arms: true`时（默认配置），设置**左臂**效果会自动同步到**右臂**。

**示例**：
```bash
# 只设置左臂，右臂自动跟随
rostopic pub /robot_led/command std_msgs/String \
  "data: '{\"region\":\"left_arm\",\"effect\":\"breathing\",\"speed\":50,\"color\":[255,0,0]}'"

# 结果：左臂和右臂都显示红色呼吸灯
```

### 7.2 独立控制右臂

如果需要左右臂不同效果，先设置左臂，再单独设置右臂覆盖：

```bash
# 1. 设置左臂（右臂自动跟随）
rostopic pub /robot_led/command std_msgs/String \
  "data: '{\"region\":\"left_arm\",\"effect\":\"breathing\",\"color\":[255,0,0]}'"

# 2. 单独设置右臂覆盖
rostopic pub /robot_led/command std_msgs/String \
  "data: '{\"region\":\"right_arm\",\"effect\":\"flowing\",\"color\":[0,0,255]}'"
```

### 7.3 禁用同步

修改配置文件：
```yaml
sync_arms: false  # 禁用手臂同步
```

重启节点后，左右臂完全独立控制。

---

## 8. 测试工具

### 8.1 自动测试脚本

```bash
# 运行完整测试
rosrun robot_led_control test_led_command.py
```

**测试内容**：
- 所有效果类型
- 速度范围（0/25/50/75/100）
- 自定义颜色
- 手臂同步

### 8.2 手动测试命令

```bash
# 测试基础效果
rostopic pub /robot_led/command std_msgs/String "data: '{\"region\":\"chest\",\"effect\":\"solid\",\"color\":[255,255,255]}'"

# 测试速度
rostopic pub /robot_led/command std_msgs/String "data: '{\"region\":\"chassis\",\"effect\":\"flowing\",\"speed\":100}'"

# 测试自定义
rostopic pub /robot_led/command std_msgs/String "data: '{\"region\":\"left_arm\",\"effect\":\"custom\",\"start_index\":0,\"rgb_data\":[255,0,0,0,255,0,0,0,255]}'"
```

---

## 9. API参考速查

### 9.1 JSON命令格式

```json
{
    "region": "chest | left_arm | right_arm | chassis | all",
    "effect": "off | solid | breathing | flowing | marquee | rainbow | custom",
    "speed": 0-100,           // 可选，默认50
    "color": [R, G, B],       // 可选，RGB 0-255
    "start_index": 0-N,       // custom模式必需
    "rgb_data": [R,G,B,...]   // custom模式必需
}
```

### 9.2 区域LED数量

| 区域 | 数量 | 索引范围 |
|------|------|----------|
| chest | 24 | 0-23 |
| left_arm | 11 | 0-10 |
| right_arm | 11 | 0-10 |
| chassis | 24 | 0-23 |

### 9.3 效果列表

| 效果 | 参数 | 说明 |
|------|------|------|
| off | - | 关闭 |
| solid | color | 常亮 |
| breathing | color, speed | 正弦波调光 |
| flowing | color, speed | 单点移动 |
| marquee | color, speed | 分组移动 |
| rainbow | speed | HSV色轮 |
| custom | start_index, rgb_data | 自定义数组 |

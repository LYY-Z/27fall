## 1. 系统概述

本系统实现机器人多部位LED灯带的控制，包括：
- **STM32端**：基于STM32F103C8T6控制4路LED灯带（胸口、左臂、右臂、底盘）
- **ROS端**：通过串口接收ROS指令，控制灯带效果
- **硬件接口**：2个PWM+DMA通道驱动WS2812/WS2815灯带

## 2. 目录结构

`led_control` 是STM32F103微控制器上运行的LED控制固件，负责接收ROS命令并驱动底盘（chassis）、胸口(chest)、左臂（left_arm）、右臂（right_arm）的LED灯效。

`robot_led_control` 是ROS节点，负责与STM32固件通信并提供用户接口。

## 3. 文档位置

**软件设计文档** 在 `/led_control/docs`
**ROS用户手册** 在 `/robot_led_control/docs`
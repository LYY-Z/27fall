## 1. 系统概述

灵巧手控制系统是一个基于ROS和STM32的机器人手控制系统，通过CAN总线实现ROS与嵌入式控制器之间的实时通信，控制4根灵巧手指的精确运动。
- **STM32端**：基于STM32F103C8T6控制8个舵机（每个手指两个舵机，对应两个自由度）
- **ROS端**：基于ROS驱动节点和CAN通信，控制舵机运动

## 2. 目录结构

`Dexterous_Hand` 是STM32F103微控制器上运行的灵巧手控制固件，负责接收ROS命令并驱动4根灵巧手指的舵机。

`dexterous_hand_can` 是ROS节点，负责与STM32固件通信并提供用户接口。

## 3. 文档位置

**STM32 设计文档** 在 `/Dexterous_Hand/docs`
**ROS 设计文档** 在 `/dexterous_hand_can/docs`
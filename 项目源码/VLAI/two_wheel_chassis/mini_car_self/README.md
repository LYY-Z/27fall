# 二轮底盘工程技术解析文档

本文基于当前仓库源码进行梳理，目标是帮助读者快速理解该二轮底盘控制工程的整体架构、模块职责、文件作用、算法实现与可维护性要点。

## 1. 项目概述

该工程是一个基于 STM32H7（`stm32h723xx`）的二轮底盘控制系统，核心特征如下：

- 主控芯片：STM32H7（高主频、FPU、丰富总线和外设）
- 通信总线：FDCAN（多路电机/上位机通信）
- 遥控输入：UART5 + DMA + 空闲中断（SBUS 帧解析）
- 执行器：两轮电机（当前主链路使用 `drv_8030`）
- 里程计：双轮速度积分得到 `x/y/yaw`
- 任务调度：自研简化调度器 `EZ_RTOS`（不是 FreeRTOS）

## 2. 目录与分层架构

工程可分为 6 层：

1. 硬件抽象层（HAL/Cube 生成）
2. BSP 层（板级外设封装）
3. 设备驱动层（电机/IMU）
4. 算法与工具层（PID、滤波、FIFO、CRC）
5. 应用任务层（控制模式、底盘控制、里程计）
6. 调度层（EZ_RTOS）

典型调用链：

`main` 初始化外设 -> 注册任务 -> `controler_task` 解析输入并写入目标速度 -> `chassis_task` 模式控制与运动学分配 -> 驱动层封包 -> `bsp_fdcan` 发送到电机。

## 3. 启动流程（按执行顺序）

入口在 `Core/Src/main.c`：

1. 使能 I-Cache/D-Cache，随后 `HAL_Init`
2. 配置系统时钟 `SystemClock_Config`
3. 初始化 GPIO/DMA/FDCAN/UART
4. 调用 `can_filter_init` 建立接收过滤和中断
5. 调用 `chassis_init` 初始化底盘状态与 PID
6. 启动 UART5 DMA 空闲接收（SBUS）
7. 添加任务 `controler_task`、`chassis_task`
8. 电机使能（节点 `0x01` 与 `0x03`）
9. 主循环中调用 `rtos_start`

## 4. 核心模块详解

### 4.1 调度层：EZ_RTOS

文件：`User/rtos/EZ_RTOS.c`、`User/rtos/EZ_RTOS.h`

功能：

- 维护固定长度任务表（`MAX_TASKS=8`）
- 任务状态：`TASK_READY` / `TASK_DELAY`
- `rtos_add_task` 注册任务函数
- `rtos_start` 轮询执行就绪任务

说明：

- 该调度器是轻量轮询式实现，不是 FreeRTOS。
- 代码中 `task_delay` 使用 `__builtin_return_address(0)` 匹配当前任务函数，属于非常规实现方式，可维护性和可移植性较弱，后续建议改为显式任务上下文。

### 4.2 控制输入层：遥控与自动模式输入

文件：`User/app/controler_task.c`、`User/uart_bsp.c`

关键点：

- `HAL_UARTEx_ReceiveToIdle_DMA` 配合空闲中断接收 SBUS 原始帧
- `sbus_frame_parse` 解 25 字节帧（11bit 通道）
- `remoteHandler` 将控制源映射为 `ctrl_mode`：
	- 保护模式 `PROTECT_MODE`
	- 遥控模式 `REMOTER_MODE`
	- 自动模式 `AUTO_MODE`
- 根据模式写入 `chassis.spd_input.vx/vy/vw`

### 4.3 底盘任务层

文件：`User/app/chassis_task.c`、`User/app/chassis_task.h`

核心流程（每次调度执行）：

1. `Chassis_mode_switch` 根据 `ctrl_mode` 选择行为回调
2. 执行当前模式回调（保护/遥控/自动）
3. `Chassis_ctrl` 下发电机速度
4. `chassis_odom_calc` 更新里程计
5. `msg_to_Host` 回传里程计
6. `task_delay(3)`

模式说明：

- 保护模式：清零输入，发送同步，清积分
- 遥控模式：按输入分配轮速并控制
- 自动模式：从 CAN 接收目标速度并做在线判定（超时降级为 0）

### 4.4 通信 BSP 层（FDCAN）

文件：`User/bsp_fdcan.c`、`User/bsp_fdcan.h`

关键能力：

- 两路 FDCAN 过滤器配置
- FIFO0/FIFO1 中断回调分发
- 接收电机反馈速度（`0x581/0x583`）
- 接收自动控制输入（`0x050`）
- 回传 odom（`0x051`）

数据解析实现：

- `chassis_automode_msg_handle` 将 8 字节 CAN 帧解析为 `vx/vy/vw/updown`
- 内置限幅（`[-800, 800]`）

### 4.5 电机驱动层

#### 4.5.1 8030 驱动（主链路）

文件：`User/drv/drv_8030.c`、`User/drv/drv_8030.h`

- 提供基于 CANopen SDO/PDO 思路的控制封装
- `MotoEnable`、`MotoSetSpeed` 为当前主流程直接调用函数
- `moto[2]` 存储反馈速度与在线状态

#### 4.5.2 DM 电机驱动（保留能力）

文件：`User/drv/drv_dmmotor.c`、`User/drv/drv_dmmotor.h`

- MIT 模式封包：`mit_ctrl`
- 浮点到定点打包：`float_to_uint`
- 反馈解析：`mf_DM_MOTOR_HANDLE`

#### 4.5.3 RobStride 驱动

文件：`User/drv/Robstride01.c`、`User/drv/Robstride.h`

- 提供使能/失能/归零/模式切换/位置控制封包
- 主要通过 `hfdcan2` 下发

#### 4.5.4 motion.c（历史兼容代码）

文件：`User/drv/motion.c`

- 采用旧式 `can.h` 风格接口，包含 PV/PP/PT 模式封装
- 与当前主链路 `fdcan + drv_8030` 风格不一致，偏历史保留

### 4.6 IMU 层

存在两套 BMI088 代码：

1. `User/imu/bmi088.c(.h)`：简洁 HAL SPI 驱动
2. `User/Device/BMI088/*`：较完整驱动 + middleware

温控任务：`User/app/imu_temp_ctrl.c`

- 读取 IMU 温度
- 简易 PID 形式调节 PWM（`htim3->CCR4`）

注意：当前 `main.c` 并未显式注册 IMU 温控任务，属于可选链路。

## 5. 算法与数据结构详解

### 5.1 运动学与里程计

文件：`User/app/chassis_task.c`

#### 5.1.1 二轮速度分配

`mini_car_calc(vy, vw, speed[])`：

- 左轮：`wheel0 = (vy + vw) * speed_pos`
- 右轮：`wheel1 = (vy - vw) * speed_pos`

本质是差速底盘映射：

$$
v_l = v + \omega, \quad v_r = v - \omega
$$

#### 5.1.2 里程计积分

`chassis_odom_calc` + `odom_update`：

- 利用轮速近似位移增量 `ds[i]`
- 线速度：`v_linear = (ds0 + ds1)/2`
- 角速度：`v_angular = (ds1 - ds0)/(2L)`（实现里含系数）
- 用中点角近似 `theta_mid = theta - dtheta/2` 提升旋转精度

### 5.2 PID 控制

文件：`User/math/pid.c`、`User/math/pid.h`

`pid_t` 结构体包含：

- `p/i/d`
- `set/get/err` 三时刻缓存
- `pout/iout/dout`
- 限幅、死区、积分限幅
- 改进位掩码 `Improve`

支持改进项：

- 梯形积分
- 变速积分
- 微分先行（框架保留）
- 微分滤波
- 积分限幅

### 5.3 卡尔曼滤波

文件：`User/math/KalmanFilter.c`、`User/math/KalmanFilter.h`

1. 一阶标量卡尔曼：`Kalman1FilterCalc`
2. 二阶矩阵卡尔曼：`Kalman2FilterCalc`

二阶实现调用 CMSIS-DSP 矩阵函数（`arm_mat_*`），适合位置-速度联合估计。

### 5.4 滤波与信号处理

主要文件：

- `math_calcu.c/.h`：斜坡、滑动滤波、二阶低通、环形误差
- `math_lib.c/.h`：通用数学工具（融合、排序、最小二乘等）
- `math_process.c/.h`：另一套斜坡/限幅/排序工具
- `func_generator.c/.h`：正弦/方波/三角/npz 信号发生器
- `ubf.c/.h`：更新缓冲与均值/加权处理

### 5.5 数据结构容器

#### 5.5.1 FIFO

两套实现：

- `fifo.c/.h`：字节和通用单元 FIFO（临界区保护）
- `data_fifo.c/.h`：依赖 `cmsis_os` 的互斥 FIFO

#### 5.5.2 内存管理

文件：`mem_mang4.c`、`mem_mang.h`

- 自定义堆分配器
- 空闲链表合并
- `heap_malloc/heap_free`

### 5.6 CRC 校验

两套实现：

- `crc.c/.h`：`crc8/crc16/crc_ccitt`
- `CRC8_CRC16.c/.h`：DJI 风格接口兼容版

## 6. 技术栈说明（结合本项目）

### 6.1 STM32 + HAL

- 外设初始化文件集中于 `Core/Src`
- 通过 CubeMX 生成基础工程，用户代码插入 USER CODE 区域

### 6.2 FDCAN

- `Core/Src/fdcan.c` 提供底层时序/引脚/中断
- `User/bsp_fdcan.c` 提供业务层过滤、收发与分发

### 6.3 UART + DMA + IDLE

- `Core/Src/usart.c` 配置 UART5（100000, 9E2，符合 SBUS 常见配置）
- 回调中重启 `ReceiveToIdle_DMA`，用于连续帧接收

### 6.4 SPI

- `Core/Src/spi.c` 配置 SPI2
- BMI088 驱动通过 SPI 读写寄存器

### 6.5 RTOS 相关说明

- 当前运行主链路为 `EZ_RTOS`
- 工程内存在一些 `cmsis_os`/`osKernelSysTick` 相关文件（多为通用库或历史代码），但并非当前主调度核心
- 因此本项目“涉及 FreeRTOS 生态接口”，但“当前控制闭环不依赖标准 FreeRTOS 任务调度器”

### 6.6 C 语言工程实践

- 模块化分层 + 头文件接口导出
- 全局结构体承载状态（如 `chassis`、`moto`、`can_spd_input`）
- 中断回调 + 主循环调度协作

## 7. 文件级说明（按目录）

以下针对 `Core` 与 `User` 目录中可见源码文件说明。

### 7.1 Core/Inc

- `main.h`：主入口公共声明。
- `gpio.h`：GPIO 初始化声明。
- `dma.h`：DMA 初始化声明。
- `fdcan.h`：FDCAN 句柄与初始化声明。
- `usart.h`：UART5 句柄、DMA 句柄与初始化声明。
- `spi.h`：SPI2 句柄与初始化声明。
- `memorymap.h`：内存映射文件头（当前为空壳）。
- `stm32h7xx_it.h`：中断函数声明。
- `stm32h7xx_hal_conf.h`：HAL 功能宏配置。

### 7.2 Core/Src

- `main.c`：系统入口、任务注册和主循环。
- `gpio.c`：GPIO 输出脚初始化。
- `dma.c`：DMA 时钟与中断优先级配置。
- `fdcan.c`：FDCAN1/2/3 初始化和 MSP 配置。
- `usart.c`：UART5 + DMA 初始化。
- `spi.c`：SPI2 + DMA 初始化。
- `memorymap.c`：内存映射实现占位。
- `stm32h7xx_it.c`：异常与外设中断服务例程。
- `stm32h7xx_hal_msp.c`：HAL 底层 MSP 框架。
- `system_stm32h7xx.c`：系统时钟与启动相关底层代码。

### 7.3 User 根目录

- `bsp_fdcan.c/.h`：FDCAN 业务封装，收发与回调分发。
- `uart_bsp.c/.h`：SBUS 帧解析与 UART 回调。

### 7.4 User/app

- `chassis_task.c/.h`：底盘主任务、模式切换、里程计。
- `controler_task.c/.h`：输入处理与控制模式决策。
- `imu_temp_ctrl.c`：IMU 温控任务。

### 7.5 User/rtos

- `EZ_RTOS.c/.h`：简化任务调度器。

### 7.6 User/drv

- `drv_8030.c/.h`：8030 电机（CANopen 风格）控制。
- `drv_dmmotor.c/.h`：DM 电机 MIT/速度模式控制。
- `Robstride01.c` + `Robstride.h`：RobStride 协议控制。
- `motion.c`：旧 CANopen 封装，疑似历史代码。

### 7.7 User/imu

- `bmi088.c/.h`：BMI088 简洁 SPI 驱动。
- `bmi088reg.h`：BMI088 寄存器定义。

### 7.8 User/Device/BMI088

- `BMI088driver.c`：BMI088 较完整驱动实现。
- `BMI088Middleware.c`：片选、延时、SPI 字节收发等中间层。
- `inc/BMI088driver.h`：驱动接口声明。
- `inc/BMI088Middleware.h`：中间层接口声明。
- `inc/BMI088reg.h`：寄存器定义。

### 7.9 User/math

- `pid.c/.h`：PID 及其改进环节。
- `KalmanFilter.c/.h`：一阶/二阶卡尔曼。
- `data_processing.c/.h`：限幅与环形误差。
- `math_calcu.c/.h`：斜坡、滤波、低通、快速数学函数。
- `math_lib.c/.h`：通用数学库与拟合函数。
- `math_process.c/.h`：斜坡、排序、延时等工具。
- `func_generator.c/.h`：多类测试信号生成。
- `fifo.c/.h`：FIFO 通用实现。
- `data_fifo.c/.h`：带互斥锁 FIFO（RTOS 风格）。
- `crc.c/.h`：CRC 工具。
- `CRC8_CRC16.c/.h`：CRC 兼容实现。
- `remote_msg.c/.h`：DR16/键鼠遥控解析（偏通用框架，含旧依赖）。
- `ubf.c/.h`：更新缓冲与窗口处理。
- `us_tim.c/.h`：微秒计时模块。
- `mem_mang4.c` + `mem_mang.h`：小型堆管理器。
- `define_printf.c`：`printf` 重定向（使用 `huart6`，当前工程需核对串口一致性）。
- `DataScope_DP.C` + `DataScope_DP.h`：上位机波形调试输出。
- `linux_list.h`：Linux 风格链表宏。
- `data_list.h`：链表数据结构补充定义。
- `macro_mutex.h`：互斥宏封装。
- `mytype.h`：通用类型定义。

## 8. 数据结构重点说明

### 8.1 `chassis_t`（底盘核心状态）

位置：`User/app/chassis_task.h`

包含：

- 模式 `mode`
- 输入/参考/反馈速度 `spd_input/spd_ref/spd_fdb`
- 轮速数组 `wheel_spd_*`
- 里程计 `odom(x,y,z)`
- 主机在线状态计数

意义：

- 该结构体是“任务层与控制层共享的单一状态容器”。

### 8.2 `pid_t`

位置：`User/math/pid.h`

包含 PID 参数、历史误差、输出、优化配置位等，是控制器最关键数据结构。

### 8.3 `s8030_moto_t` 与 `dmmoto_msg_t`

位置：`User/drv/drv_8030.h`、`User/drv/drv_dmmotor.h`

- 存储电机实时反馈（速度、位置、在线）
- 提供上层控制闭环输入

### 8.4 FIFO/UBF 结构

- `fifo_s_t`：环形缓存基础结构
- `ubf_t`：按时间索引读取历史数据的更新缓冲

## 9. 与 FreeRTOS 的关系说明

你要求的“FreeRTOS 相关解释”在本工程中的实际情况如下：

1. 主调度器不是 FreeRTOS，而是 `EZ_RTOS`。
2. 工程中有部分源文件带有 CMSIS-OS/FreeRTOS 风格接口痕迹（如 `osKernelSysTick`、`osMutex`），主要来自历史通用组件。
3. 如需完整迁移到 FreeRTOS，可将 `controler_task/chassis_task` 封装为 `xTaskCreate` 任务，并用 `vTaskDelay` 替代当前延时机制。

## 10. 当前代码可维护性观察

### 10.1 优点

- 模块边界清晰（app/drv/bsp/math）
- 通信与控制逻辑分离
- 具备较完整工具库（滤波、FIFO、CRC、信号发生）

### 10.2 风险点

- `EZ_RTOS` 的 `task_delay` 实现方式非常规
- 同时保留多套历史库（`remote_msg`、`data_fifo`、`motion.c`），易引入依赖冲突
- 某些文件引用 F4 头文件或旧接口，需要确认是否参与编译
- `DataScope_DP.C`、`.orig` 文件属于历史/备份资产，建议清理或隔离

## 11. 建议的后续优化方向

1. 明确“主链路文件”与“历史保留文件”边界，减少认知负担。
2. 为 `EZ_RTOS` 增加显式任务上下文（避免返回地址匹配）。
3. 统一数学工具库，消除重复实现（如多处 `circle_error`、`abs_limit`）。
4. 补充模块级单元测试：PID、里程计、CAN 帧解析。
5. 在 README 之外新增 `docs/`，沉淀通信协议与参数标定手册。

---

如果你希望，我可以在下一步继续生成：

- 一份“按函数级别”的深入注释版文档（逐函数解释输入/输出/边界条件）
- 一份“新成员 30 分钟上手指南”（包含调试路径、常见故障排查）
- 一份“控制参数标定手册模板”（PID/速度环/里程计系数）
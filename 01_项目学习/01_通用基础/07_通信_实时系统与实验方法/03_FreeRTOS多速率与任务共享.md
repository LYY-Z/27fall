# 03 FreeRTOS多速率与任务共享

先修：[02_CANFDCAN协议与电机反馈](02_CANFDCAN协议与电机反馈.md)。项目：P1—P7。目标：明确接口、时效、恢复和可追溯实验记录。

## 1. 任务把工作分开，但共享状态仍要设计

嵌入式系统可有IMU、控制、通信、遥控和保护任务。各任务有优先级、栈和调度条件；中断与任务分工。不能在中断里做长计算/阻塞调用；具体ISR安全API按所用FreeRTOS版本查。

P3/P7源码里的delay、任务创建与条件分支说明配置意图，实际耗时和周期需测量。把delay值直接称“实测控制1000Hz”没有证据。

## 2. 共享快照的手算

IMU结构体包含roll=.1与gyro=.2；写任务先把roll改.12，尚未更新gyro=.4，读任务在中间读到(.12,.2)，拼成不同时间的数据。对整个状态快照同步/复制比逐字段随意读取可靠。

mutex/临界区/队列/双缓冲选择取决于中断上下文、响应时间与对象大小。`volatile`不能保证多个字段一致。持锁做CAN/网络阻塞发送会扩大抖动。

## 3. 多速率实际算周期

传感读取每1ms，姿态控制每2ms，位置外环每20ms：配置频率1000/500/50Hz。若姿态计算耗3ms，它不可能按2ms完成，需要记录deadline miss并调整，不是任务优先级高就会完成。

每环dt用真实有效时间差或明确设计周期；状态新鲜度与旧数据最大年龄要定义。若外环每20ms用dt=2ms积分，积分效果少10倍。

## 4. 初始化与停止

先建立硬件与队列、确认传感/电机反馈、校准零位，再使能闭环。掉线/跌倒进入保护状态时输出归零或按明确停机策略，重启前确认反馈与积分状态，避免旧命令突然恢复。

任务退出/重启也要保护对象寿命，桌面C++线程实验只说明同步原理，不是可直接烧进STM32的调度配置。

## 5. 实验、失败与英文

[线程队列实验](../../03_代码实验/01_基础实验/03_数据结构与状态同步/README.md)理解快照与停止；P3/P7读实际task。失败：优先级反转；栈不足；共享字段竞争；周期超时仍积分固定dt；保护分散多个回调互相覆盖。

“I separate acquisition, control and communication tasks and define how they share a consistent state. Configured periods are not measured timing, so I log execution time, jitter and missed deadlines.”

追问：Why not put everything in the highest-priority task? Long work can block time-critical acquisition and communication, and shared resource blocking remains.

1. 概念：RTOS自动保证稳定吗？答：只是调度与同步工具，控制/时序还需设计。
2. 计算：2ms任务耗3ms，超时多少？答：至少1ms超过预算。
3. 代码：两字段快照如何同步？答：按上下文使用适当短保护/队列/缓冲，不靠volatile。
4. 解释：平均频率对但偶发倒？答：查最大延迟/错过周期、状态有效性、保护与接触。

下一章：[04_设备生命周期通信与状态机](04_设备生命周期通信与状态机.md)。

## 精读补充：把中间步骤讲清楚

### A. delay与固定释放时刻不同

若任务计算.8ms后再delay3ms，理想周期间隔约3.8ms，加上调度还会变。若按上一释放时刻延后3ms调度，目标周期3ms，但计算超过周期仍会错过deadline。代码写3ms不能直接报告333.3Hz实测。

读取电机角/速度/时间戳时，整份快照一致；锁内只复制，耗时计算在锁外。中断API、优先级、栈和硬件驱动另按原平台，桌面thread不是FreeRTOS任务的直接替换。

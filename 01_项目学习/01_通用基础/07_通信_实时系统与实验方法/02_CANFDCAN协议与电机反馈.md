# 02 CANFDCAN协议与电机反馈

先修：[01_ROSROS2消息TF与回调](01_ROSROS2消息TF与回调.md)。项目：P1—P7。目标：明确接口、时效、恢复和可追溯实验记录。

## 1. CAN报文不是任意长JSON

CAN使用标识符仲裁和有限payload传输，节点收到报文后按约定解析；经典CAN数据最多8字节，CAN FD数据字段可到64字节。FDCAN是MCU相关控制器/外设接口名，是否用FD格式、波特率和数据段设置要看配置。

CAN ID的作用按协议决定，不能凭ID说某电机。多字节位置、电流、温度和状态的端序、比例、有符号解释必须从设备说明与源码对应。把同一8字节数据换协议解释会得完全不同数字。

## 2. 手算端序与比例

教学两字节大端速度[0xFF,0x9C]→无符号65436，按16位补码解释为-100。若比例.01rad/s/count，速度-1rad/s。误当无符号会变654.36rad/s，绝不能用滤波修复。

另一基础packet实验是小端uint32序号+float32值，严格8字节；它是教学应用格式，不是实际RoboMaster电机CAN协议。

## 3. 反馈怎样进入闭环

接收中断/回调→验证ID与长度→解析→更新电机状态和last_seen→控制任务读一致快照→计算电流/力矩命令→打包发送。先检查电机反馈是轴角/速度/电流，力矩常由电流和电机常数估计，有齿比/效率影响。

轮角多圈展开需处理编码器周期与采样；若反馈太慢可能跨多圈，简单相邻差展开不可靠。CAN重发/错误处理不自动保证每个控制deadline前到达，总线负载和仲裁也影响。

## 4. 超时的数字例子

当前t=1.000s，某电机last_seen=.950，年龄50ms。若设计上限30ms，则状态失效，不能继续用最后速度假装当前有效。超时阈值需由实际周期、网络和安全设计确定，本数值只是例。

## 5. 实验、失败与英文练习

[packet实验](../../03_代码实验/01_基础实验/12_搜索图像与协议/README.md)先理解字节解码；P3/P7会解释实际ID、任务和发送路径。失败：端序、有符号、齿比错；电机ID冲突；初始化前发命令；超时未停；限幅单位错。

“A CAN frame must be decoded with the device protocol's byte order, scaling and sign convention. I track feedback freshness and define what the controller does when an actuator stops reporting.”

追问：Does CAN reliability guarantee a real-time deadline? No. Arbitration, bus load and processing delays still matter.

1. 概念：8字节可任意解释吗？答：需双方一致应用协议。
2. 计算：0xFF9C有符号16位？答：-100。
3. 代码：长度6却读第8字节？答：拒绝，不越界。
4. 解释：电机反向先调PID吗？答：先查轴正向/协议符号/安装与齿比。

下一章：[03_FreeRTOS多速率与任务共享](03_FreeRTOS多速率与任务共享.md)。

## 精读补充：把中间步骤讲清楚

### A. 符号、缩放与齿比按顺序处理

字节FF9C解补码为−100，若编码的是电机rpm，先得到−100rpm，再乘2π/60得−10.472rad/s。若电机与轮子减速比10，轮速−1.0472rad/s；轮半径.1m时线速−.10472m/s。缺一项就可能差10倍或60/2π倍。

反馈电流与命令电流字段不一定同缩放，更不一定就是N·m。必须按型号协议读实际CAN ID、长度、单位；教学packet格式不冒充设备协议。

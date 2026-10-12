# P7 简历、PS 与源码证据对应

## 1. 使用原则

以下表格说明“课程代码能证明什么”，不替申请者声明个人贡献。申请材料中的“我设计/实现/调试/验证”必须再由个人提交记录、版本提交、实验日志或团队分工证明。

|可描述的主题|仓库中能追到的依据|谨慎表述|不能仅凭源码声称|
|---|---|---|---|
|五连杆正逆运动学|第五课 MATLAB forwardKinematics.m、inverseKinematics.m；第十一课 Kinematics.cpp|学习或分析了闭链几何与候选分支|实物尺寸完全标定、全工作空间可达|
|PID 平衡入门|第六课 robot.cpp、PID 文件和 MPU6050 文件|课程实现展示 PID 与传感反馈的基本控制路径|实机长期稳定、某个性能提升百分比|
|从物理模型推导 LQR|第八课 wheel_control.m 中 A、B、Q、R 与 lqr 调用|按简化倒立摆模型建立四状态连续模型并计算反馈增益|完整轮腿系统精确动力学、部署成功的硬件效果|
|腿高相关轮反馈系数|第九课 LQRfitting.m 用三个硬编码样本做二次拟合；第九课控制函数硬编码增益；第十一课另有腿高相关系数函数|学习了腿高变化时轮反馈系数可以变化，并能区分离线拟合样例与控制中实际调用|不能说第九课脚本自动生成了样本；不能把第九课硬编码系数说成在线增益调度；第九课与第十一课是不同课程快照|
|腿部 VMC|第十一课 calRightVMC、calLeftVMC 与 CAN_Control|将腿端虚拟力通过闭链几何映射到关节 torque 字段|真实输出力矩已校准或达到特定性能|
|传感、任务和通信|第十一课 MPU6050、IMUTask、CAN/TWAI 和主 loop|分析 ESP32 任务与腿部 CAN 命令链|实测 1 kHz、完整失联保护、没有数据竞争|
|控制周期|第十一课 main.cpp 调用顺序|梳理轮反馈、VMC、遥控和命令的调用先后|循环时间、闭环带宽和稳定裕度，除非有同步日志|

## 2. 面试中可以安全使用的说法

如果确实是课程学习：

> I studied a wheeled-bipedal robot control codebase and traced its linkage kinematics, balance-control examples, and VMC-to-joint-command path.

如果确实亲自做了模型推导或离线复现，要明确实验边界：

> I independently reproduced the four-state inverted-pendulum model and compared the derived state-space coefficients with the MATLAB script. This was an offline learning exercise rather than a claim of validated hardware performance.

若确有团队/个人实机经历，再补可核实的板卡、传感器、测试条件、指标和个人角色。不要把仓库已有代码自动算成个人实现。

## 3. 明确存在的源码核对点

- 第八课运动方程消元得到的 B 第四项与脚本写法有符号差异，简历不要声称已完成一致性验证，除非已解决并留有记录。
- 第九课拟合样本直接写在脚本中；它没有在同一脚本里生成不同高度下的 LQR 样本。
- 第九课与第十一课多项式系数不是同一组，必须按版本分别引用。
- 第十一课轮电机接口实现位于预编译库，目标单位需要补证。
- 第十一课有并行 IMU 任务和主循环共享变量；周期和数据时效需要实测。

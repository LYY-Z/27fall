# 03 低通互补与Mahony滤波

先修：[02_IMU比力重力坐标与漂移](02_IMU比力重力坐标与漂移.md)。项目：P1、P3、P7。学习目标：说清数据来源与统计假设，完成本章手算，再读代码。

## 1. 平滑为什么会变慢

一阶低通y_k=αy_{k-1}+(1-α)z_k，0≤α<1。当前读数只贡献一部分，旧值继续保留。手算α=.8，旧输出0，输入从0跳1，输出依次.2、.36、.488，逐渐接近1。噪声减小，真实快速变化也被推迟。

常见由连续时间常数τ用后向Euler取α=τ/(τ+dt)；另一离散法取exp(-dt/τ)，不要混说是同一精确离散。固定α但改变dt会改变物理滤波时间常数。

## 2. 互补公式每个值从哪里来

\[\theta_k=\alpha(\theta_{k-1}+\omega_{gyro,k}\Delta t)+(1-\alpha)\theta_{acc,k}.\]

θ_old是上次融合角，不是上次陀螺读数。ω_gyro是已统一符号、可减偏置的角速度rad/s；dt秒；θ_acc从比力方向atan2估计的角rad；α无单位。

先用陀螺预测θ_pred=θ_old+ωdt，再用重力参考纠正：(1-α)(θ_acc-θ_pred)。不是把角速度和角度直接相加。

完整手算：θ_old=.1rad,ω=.2rad/s,dt=.01s，预测.102；θ_acc=.09,α=.98。融合=.98×.102+.02×.09=.10176rad。加速度参考只让预测向.09移动2%，没有把当前变化完全抹掉。

## 3. 互补“快与稳”有条件

陀螺短期跟踪角变化，长期偏置漂移；重力参考帮助低频校正roll/pitch。平移加速度强时重力参考被污染，要降低权重或拒绝异常，不是加速度计天然永远可靠。

angle_acc=atan2(f_y,f_z)只对应已声明轴约定的roll。普通重力观测不能决定绕重力方向的yaw；有磁力计、视觉等额外方向才可约束该自由度。角跨界时先按周期求最短差，不直接平均179°与-179°得0°。

## 4. Mahony与简单单轴式的连接

Mahony类非线性互补滤波直接在三维旋转空间工作：用观测方向与预测方向的差形成姿态校正，并可估计陀螺偏置；姿态用旋转矩阵或四元数更新。它不是简单对roll/pitch/yaw逐个做同一平均。

方向叉积的误差大小与方向不一致有关；比例校正方向，积分部分估计长期偏置。实际符号、权重、磁力计使用、归一化和dt按实现检查。本轮实验只实现单轴互补，不声称完整Mahony。

该方法与偏置估计见[Mahony等2008原论文信息](https://researchportalplus.anu.edu.au/en/publications/nonlinear-complementary-filters-on-the-special-orthogonal-group/)，查阅2026-10-02。

## 5. 实验和失败

[互补实验](../../03_代码实验/01_基础实验/06_IMU与互补滤波/README.md)改变α、陀螺偏置和加速度角污染，比较漂移/响应。失败：把degree与rad混合；dt≤0；强运动仍完全信加速度；两重滤波延迟过大。

## 6. 英文与练习

“A complementary filter integrates the gyro for short-term changes and uses a gravity-based angle to correct long-term drift. The accelerometer weight should decrease when translational acceleration makes the gravity reference unreliable.”

追问：Can gravity correct yaw? No; rotation around gravity leaves the measured gravity direction unchanged.

1. 概念：α=.98信测量98%吗？答：信陀螺预测98%，加速度参考2%。
2. 计算：α=0上例？答：直接θ_acc=.09rad。
3. 代码：变量theta写degree，gyro用rad/s怎么办？答：先统一rad。
4. 解释：平滑更强却平衡振荡？答：延迟使反馈过时，要检查闭环相位和带宽。

下一章：[04_Kalman一维推导与融合](04_Kalman一维推导与融合.md)。

## 精读补充：把中间步骤讲清楚

### A. 互补公式每个量的身份

θ_old是上周期融合角度，ω_gyro是本次角速度，dt是两次更新之间秒数，θ_acc是按轴定义算出的倾角，α是无单位权重。前三者组成预测θ_pred=θ_old+ωdt；再算θ_new=θ_pred+(1−α)(θ_acc−θ_pred)。后一写法显示加速度参考只是修正预测差的一部分。

θ_old=10°，陀螺2°/s，dt=.1s，预测10.2°；加速度倾角9.2°、α=.9，修正.1×(−1°)=−.1°，结果10.1°。一组角度全部用degree也可算，但不可把rad/s直接乘dt加到degree。三维陀螺分量通常不等于欧拉角导数，这个例子是一轴近似。

### B. 改周期时为何α要跟着变

一阶互补常取α=τ/(τ+dt)。τ=.5s时dt=.01得到.98039，dt=.1得到.83333。固定α=.98却把周期放慢十倍，单位时间的校正速度也改变。检查公式中α究竟给旧值还是新值；P1源码的低通β给新样本，和这里α的含义相反。

Mahony还需要姿态与重力方向误差、角速度校正及可选偏置估计；不能把上面一轴加权公式说成完整Mahony实现。

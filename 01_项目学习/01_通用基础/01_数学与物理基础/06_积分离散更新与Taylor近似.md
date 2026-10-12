# 6. 积分、离散更新与Taylor近似

先修：[时间导数](05_导数偏导与链式法则.md)。项目：全部控制、P2/P5/P7。代码连接：[运动学](../../03_代码实验/01_基础实验/05_运动学与雅可比/README.md)、[LQR](../../03_代码实验/01_基础实验/09_LQR与Riccati/README.md)。下一章：[最小二乘与伪逆](07_范数最小二乘与伪逆.md)。

## 1. 积分是把变化累积起来

速度3m/s持续2s，位置增加6m。速度分两段：前1s为2m/s，后1s为4m/s，距离2×1+4×1=6m。把很多小时间段的“速度×持续时间”加起来，就是积分：

\[
x(t_1)-x(t_0)=\int_{t_0}^{t_1}v(t)dt.
\]

被积函数v是m/s，dt是s，乘后是m。积分符号不是把数字无限变大，而是连续累积。速度有负号时，位置变化有正负相抵；这与行驶路程用速度大小累积不同。

## 2. 计算机只能每隔一个周期更新

记录每个周期当前速度vk，假设这小段时间速度近似不变：

\[
x_{k+1}\approx x_k+v_k\Delta t.
\]

这叫前向Euler更新。比如x=1m，v=.2m/s，dt=.1s，下一位置近似1.02m。机器人在两次计算之间仍连续运动，k只是计算记录编号。

陀螺积分同理：θ_next≈θ+ωdt。若陀螺偏置b=.01rad/s，即使真实静止，100s后积分角度偏1rad，约57.3°。积分会累积系统性偏差，不会自动抵消。

## 3. 为什么位置还有半个加速度项

假设一个周期内加速度u恒定，初速度v。经过τ秒，速度v(τ)=v+uτ。位置变化：

\[
\Delta x=\int_0^{\Delta t}(v+u\tau)d\tau
=v\Delta t+\frac12u\Delta t^2.
\]

第一项是“如果保持初速度，本来会走的距离”；第二项是“因为速度在这段时间增加，额外走的距离”。从速度时间图看，额外部分是底dt、高u dt的三角形面积，所以1/2。

v=1m/s，u=2m/s²，dt=.5s：保持初速度走.5m；速度增加1m/s，额外面积.5×.5×1=.25m；总.75m。末速度2m/s，平均速度(1+2)/2=1.5，乘.5也得.75m。

u为负时第二项负，表示减速后比维持初速度走得少。若途中速度变负，算的是净位移，不是总路程。

## 4. 位置速度一起写成A/B

令状态s=[位置误差e,速度v]^T，u是加速度，目标位置固定：

\[
e_{next}=e+v\Delta t+\frac12u\Delta t^2,
\quad v_{next}=v+u\Delta t.
\]

将当前状态贡献和输入贡献分别排起来：

\[
s_{next}=\begin{bmatrix}1&\Delta t\\0&1\end{bmatrix}s
+\begin{bmatrix}\Delta t^2/2\\\Delta t\end{bmatrix}u.
\]

这就是离散双积分模型A/B的来源。u必须真的是模型中的加速度，若接口是电流、轮矩或速度参考，还需要执行器/动力学关系，不能直接把同一个B套上去。

e定义当前位置减目标时速度贡献+v；若e定义目标减当前，符号相反。移动目标也需要参考速度，不再是固定目标的这个模型。

## 5. Taylor近似在说什么

函数在一个点附近展开：

\[
f(q+\Delta q)\approx f(q)+f'(q)\Delta q.
\]

当前值＋当前位置斜率×输入微小变化。比如f(q)=q²，q=2，Δq=.1：近似4+4×.1=4.4；真实2.1²=4.41，漏掉的.01就是(Δq)²。

如果Δq=1，近似8，真实9，误差明显大。局部线性化的小步条件在数字里能看见。

多变量：\(f(q+\Delta q)\approx f(q)+J(q)\Delta q\)。速度形式令Δq≈q̇dt，所以x_next≈x+Jq̇dt。

## 6. 关节更新后为什么重新算FK

P2 IK算出q̇后，先q_next=q+q̇dt，再用FK算实际模型位置f(q_next)。`x + J q_dot dt`只是一阶预测；FK按照更新后姿态算几何位置，不把局部J冻结到大步长。

也要注意：q的Euler更新本身对随时间变化的q̇仍是近似，重新FK不等于整个积分都变精确。

## 7. 代码与离散误差

```python
dt = 0.5
position = 0.0
velocity = 1.0
acceleration = 2.0
position_next = position + velocity*dt + 0.5*acceleration*dt**2
velocity_next = velocity + acceleration*dt
```

先用旧velocity更新position，再写新velocity。如果先覆盖velocity，再套旧速度公式，会把加速贡献多算。所有状态同时更新时先保留旧状态或用数组计算新状态。

失败：dt用ms却当s；时间戳重复/乱序使dt≤0；使用新速度和旧加速度混合更新；步长过大影响精度甚至数值稳定。

减小步长不解决模型本身错误；速度偏置、漏掉重力或轮子打滑仍会积累。

## 8. 英文与练习

English: “The extra half-acceleration term accounts for the velocity change during the interval. It is exact for constant acceleration over that interval, while a forward Euler update is generally only a first-order approximation.”

追问：How do you choose dt? Why recompute forward kinematics after integrating joint velocity?

练习：①v=0,u=1,dt=.2，位置和速度变化？②q=1,q̇=-.5,dt=.1，q_next？③用新速度计算位置有什么风险？④快速改变目标时双积分误差模型需要补什么？

答案：①Δx=.5×1×.04=.02m，Δv=.2m/s。②.95rad。③公式可能重复计入加速度，要按所选积分方法一致计算。④参考位置、速度和加速度的变化，以及实际执行器动力学。

## 精读补充：把中间步骤讲清楚

### A. 减速也有“半个加速度项”

初速度2 m/s、加速度−1 m/s²、持续1 s，末速度1 m/s。位移2×1+.5×(−1)×1²=1.5 m，也等于平均速度(2+1)/2乘时间。负加速度不代表本周期位移为负，只是比保持初速度走得少。

若持续3 s，末速度−1 m/s，净位移6−4.5=1.5 m；中间先前进、停下、再后退。行程要分别累计各段速度的绝对值，不等于净位移。

### B. 连续模型稳定，Euler也可能数值发散

例如xdot=−20x，真实解x(t)=x₀e^(−20t)，会衰减。Euler给x_next=(1−20dt)x。dt=.02时倍率.6，衰减；dt=.1时倍率−1，来回翻号不衰减；dt=.2时倍率−3，数值越算越大。

这说明步长会改变数值更新的稳定性。不能因为原方程稳定，就把任意dt下的模拟轨迹当真实系统。减小dt有助这个近似，但不能修复错模型或传感器偏置。

### C. 更新顺序怎么写才清楚？

先保存old_position、old_velocity，再用同一旧时刻状态计算两个new值，最后一起赋回。若故意用新速度更新位置，则是另一种积分方法，需明确写出；不能把它同时称为本章恒加速度的精确一步公式。

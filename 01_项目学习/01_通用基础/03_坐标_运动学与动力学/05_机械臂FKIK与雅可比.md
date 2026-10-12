# 05 机械臂FKIK与雅可比

先修：[04_四元数乘法双覆盖与SLERP](04_四元数乘法双覆盖与SLERP.md)。项目：P2、P7。学习目标：能解释本章几何/物理关系，完成手算并识别失败条件。

## 1. 先认识角度和末端位置

两根连杆长度l₁,l₂，q₁从固定x轴逆时针量，q₂从第一杆到第二杆的相对角。第二杆绝对方向q₁+q₂：

\[x=l_1\cos q_1+l_2\cos(q_1+q_2),\quad y=l_1\sin q_1+l_2\sin(q_1+q_2).\]

FK输入关节角算位置；IK输入位置求角。由余弦定理cosq₂=(x²+y²-l₁²-l₂²)/(2l₁l₂)，通常q₂有±两支。q₁=atan2(y,x)-atan2(l₂sinq₂,l₁+l₂cosq₂)。目标距离超出|l₁-l₂|到l₁+l₂之间时无解；关节限位/碰撞还可能排除几何解。

## 2. 为什么对时间求导得到矩阵

x=f(q₁(t),q₂(t))。短时间内角变化Δq₁、Δq₂，各自引起的x变化近似(∂x/∂q₁)Δq₁+(∂x/∂q₂)Δq₂。除Δt并取极限得到ẋ=(∂x/∂q₁)q̇₁+(∂x/∂q₂)q̇₂；y同理。

把两条等式叠起来，系数必须按“每行一个输出，每列一个输入”放：

\[
\begin{bmatrix}\dot x\\\dot y\end{bmatrix}=
\underbrace{\begin{bmatrix}-l_1\sin q_1-l_2\sin(q_1+q_2)&-l_2\sin(q_1+q_2)\\l_1\cos q_1+l_2\cos(q_1+q_2)&l_2\cos(q_1+q_2)\end{bmatrix}}_{J(q)}
\begin{bmatrix}\dot q_1\\\dot q_2\end{bmatrix}.
\]

q̇=[q̇₁,q̇₂]ᵀ是2×1列向量，单位rad/s；NumPy用形状(2,)表达同一组分量。J元素m/rad，乘后末端m/s。J依赖当前q，不是永远相同。

## 3. 完整手算与局部意义

l₁=l₂=1m，q₁=0,q₂=π/2，FK=[1,1]，J=[[-1,-1],[1,0]]。q̇=[.1,.2]rad/s，末端速度[-.3,.1]m/s。

dt=.01s，q_next=[.001,π/2+.002]，末端线性近似[.997,1.001]。真实下一位置应再算FK，因sin/cos非线性会有高阶差异。J第1列是只让关节1以1rad/s动的末端速度，第2列同理；一个关节同时影响x和y。

## 4. 奇异为何“某个方向没了”

detJ=l₁l₂sinq₂。q₂=0伸直时J=[[0,0],[l₁+l₂,l₂]]，一阶速度只能沿y，x速度为0。机器人可通过有限幅度弯曲改变x，但不能在该瞬间实现任意指定ẋ。

近伸直时弱方向奇异值很小，反解可能要求大q̇；恰好零时伪逆把该方向倒数置零，留下不可实现残差。q̇=J⁺v只给最小范数最小二乘解，不处理限位/碰撞。阻尼解min||Jq̇-v||²+λ²||q̇||²，用稳定输入交换残差。具体推导见[伪逆](../01_数学与物理基础/07_范数最小二乘与伪逆.md)。

## 5. 力与速度用不同映射

速度v=Jq̇；功率Fᵀv=τᵀq̇要求τ=JᵀF。Jᵀ不是速度反解。力和速度必须同系、同一参考点；外力作用在机器人上与机器人施给环境的力符号相反。

六维任务包含线速度与角速度，角速度不是简单的欧拉角三个导数。几何雅可比与姿态参数的解析雅可比要区分，力旋量排列与J配对。

## 6. 代码、失败与英文

[运动学实验](../../03_代码实验/01_基础实验/05_运动学与雅可比/README.md)比较解析J与中心差分，给直腿秩与不可达IK。失败：角度度数混弧度；把局部速度积分很久不更新J；把求解有数字当可执行。P2约束IK与P7闭链需要进一步模型。

“The Jacobian is the derivative of forward kinematics at the current configuration. Each column describes how one joint affects all task-velocity components. A pseudoinverse solves velocity commands, while the transpose maps a compatible endpoint force to joint torque.”

追问：Can the arm change the unavailable coordinate at all? It may change it through finite nonlinear motion, but the instantaneous first-order velocity direction is lost at the singularity.

1. 概念：q̇是角度还是速度？答：每关节角变化率。
2. 计算：上例q̇=[0,.2]？答：v=[-.2,0]。
3. 代码：给[3,0]m目标、两杆各1m？答：明确不可达，不能强行acos越界。
4. 解释：阻尼解有限但末端不跟踪？答：看残差、弱方向与限幅；有限输出不等于精确实现。

下一章：[06_差速全向麦轮与球轮运动学](06_差速全向麦轮与球轮运动学.md)。

## 精读补充：把中间步骤讲清楚

### A. 同一个末端点为什么有两个关节解？

两杆各1，目标[1,1]。cosq₂=(2−1−1)/2=0，所以q₂=+90°或−90°。第一支q₁=0，第二杆绝对角90°；第二支q₁=90°，第二杆绝对角0。两种都到[1,1]，但肘部位置不同。

选解要看当前关节离哪支近、限位、碰撞和轨迹连续性。不能只把acos返回的第一支当唯一物理解。

### B. 反解局部速度怎样手算？

在第一支J=[[-1,−1],[1,0]]，目标末端速度[.1,0]。第二行给qdot₁=0；第一行−qdot₁−qdot₂=.1，所以qdot₂=−.1 rad/s。末端向正x的局部运动由第二关节负向转动产生，不是“qdot₁对应x”。

dt=.1后q₂减.01 rad，实际末端沿圆弧变化。雅可比只给当前切线，长时间重复同一个J会错；下一周期需要更新几何。

### C. 6维速度的角部分要配套

v_task=[v_x,v_y,v_z,ω_x,ω_y,ω_z]与相同次序的力旋量[F_x,F_y,F_z,M_x,M_y,M_z]做功率配对。若库先放角速度，J行和力矩顺序也要改；欧拉角变化率不是任意姿态下的ω。

# MuJoCo、Mink、任务约束与求解

## 0. 从目标到下一小步：本章在回答什么

上一章产生 TCP 的目标位姿。这里要知道机器人当前在哪里，再决定肩、肘、腕等关节各自怎样动。**正运动学**从关节状态算末端；**逆运动学 IK**从末端要求反算关节动作。差分 IK 在当前姿势附近求一步，更新后重新算，适合持续变化的遥操目标。

教学推导、当前上游 API 和本地源码分别标明。源码入口在[文件地图](../02_源码阅读与运行/01_源码版本与文件地图.md)，[完整周期](../02_源码阅读与运行/02_一个周期的调用与数据流.md)负责连接前后模块。本轮只读源码和编辑文档，未运行机器人程序。

## 1. 位置、朝向、误差和速度依次出现

### 1.1 先得到两种误差

统一使用 B 为基座、E 为 TCP，\(R_{AB}\) 将 B 向量映到 A。当前和目标都表达在 B：
\[
e_p=p_d^B-p_E^B\quad({\rm m}),\qquad
e_R=\operatorname{Log}(R_dR_{BE}^T)^\vee\quad({\rm rad}).
\]
\(R_dR_{BE}^T\) 描述还要按 B 轴转多少，Log/vee 取出 \(\theta n\) 形式的三维轴角。它不是把旋转矩阵九个数字逐格取对数，也不是四元数的四个分量相减。若采用 \(R_{BE}^TR_d\)，轴角按 E 局部轴描述，雅可比也要换到同一表达系。

教学例：当前位置 \([0.40,0.23,0.30]\) m，目标 \([0.40,0.25,0.30]\) m，所以 \(e_p=[0,0.02,0]^T\) m。当前和目标只绕同一 B-z 轴，yaw 分别为 104° 和 110°，所以 \(e_R=[0,0,0.10472]^T\) rad。欧拉角差仅在这种简单例子中适用；一般三维旋转要整体比较。

### 1.2 米乘“每秒系数”为什么是速度

这是控制设计选择的一条反馈规则：
\[
v_d=K_pe_p,\qquad\omega_d=K_Re_R.
\]
想用约 T 秒纠正当前距离，可先选 \(K=1/T\)。单位上 \( {\rm m}\times{\rm s}^{-1}={\rm m/s}\)，弧度也同理。它不是位置天然变成速度，而是指定“误差越大，先靠近得越快”。目标不动时，离散更新 \(e_{k+1}\approx(1-Kdt)e_k\)，每轮重算会逐渐减小速度，通常不会恰好在 T 秒零误差。

取 \(K_p=2/{\rm s},K_R=3/{\rm s}\)，上述误差产生
\[
v_d=[0,0.04,0]^T\ {\rm m/s},\quad
\omega_d=[0,0,0.31416]^T\ {\rm rad/s}.
\]
把它们上下排列为
\[
V_d=\begin{bmatrix}v_d\\\omega_d\end{bmatrix}
=[0,0.04,0,0,0,0.31416]^T.
\]
前三项线速度，后三项角速度。**并排记录六种要求，不是米与弧度相加。**任务权重/尺度让不同单位的残差在优化中可比较，也会影响解的偏好。这里 K 的单位是 1/s；后面 Mink 的每步 gain 是另一种定义，不要直接照抄数值。

## 2. 模型和关节角怎样算出轴心、轴向和 TCP

### 2.1 机器人模型存了什么

MJCF/XML 或 URDF 描述连杆连接、每个关节固定安装变换、转动/移动轴、TCP 固定偏移。动力学还要质量、质心和惯量；只求 FK/Jacobian 时，关键是几何和当前关节状态。模型中局部轴和局部原点不能直接当作本周期世界轴、世界位置。

对一条从基座到末端的链，设父连杆到关节的固定变换为 \(T_{L_{i-1}J_i}\)，关节运动变换为 \(Q_i(q_i)\)，关节到子连杆还有固定安装变换 \(T_{J_iL_i}\)。沿链递推：
\[
T_{BJ_i}=T_{BL_{i-1}}T_{L_{i-1}J_i},\qquad
T_{BL_i}=T_{BJ_i}Q_i(q_i)T_{J_iL_i}.
\]
转动关节 \(Q_i\) 绕模型给定局部单位轴旋转；移动关节沿轴平移。实际 MJCF/URDF 的结构和原点定义会不同，这个分解是在解释递推原理，不能硬套字段。

本周期轴心与单位轴在 B 中为
\[
O_i^B=p_{J_i}^B,\qquad a_i^B=R_{BJ_i}a_i^{J_i}.
\]
最后 \(T_{BE}=T_{BL_n}T_{L_nE}\)，取右上块得到 TCP 的 P，取左上块得到朝向。前面关节转动会改变后面所有轴心和轴向，因此每轮都由当前 q 重新递推。

### 2.2 二连杆完整几何例：没有先试动

两根长 \(l_1=0.30\) m、\(l_2=0.20\) m 的杆在 xy 平面运动，两轴均沿 +z。当前 \(q_1=90^\circ,q_2=0\)：
\[
O_1=[0,0,0]^T,\quad
O_2=[l_1\cos q_1,l_1\sin q_1,0]^T=[0,0.30,0]^T,
\]
\[
P=[l_1\cos q_1+l_2\cos(q_1+q_2),
l_1\sin q_1+l_2\sin(q_1+q_2),0]^T=[0,0.50,0]^T.
\]
前一关节使第二轴心来到 +y；程序用模型和角度直接计算，不要求电机先转到某处试测。

## 3. 几何雅可比一列怎样从叉乘出来

### 3.1 转动关节：切线线速度与轴向角速度

单位角速度绕轴 a 转，末端相对轴心的向量为 \(r=P-O\)，所以
\[
J_i=\begin{bmatrix}a_i\times(P-O_i)\\a_i\end{bmatrix}.
\]
上三项来自圆弧切线，下三项来自绕同一轴改变朝向。a、P、O 必须在同一参考系表达，且 a 是单位向量。叉乘的逐项规则是
\[
a\times r=
[a_yr_z-a_zr_y,\ a_zr_x-a_xr_z,\ a_xr_y-a_yr_x]^T.
\]

先用单杆：\(a=[0,0,1],O=[0,0,0],P=[0.30,0,0]\)：
\[
a\times(P-O)=
[0\cdot0-1\cdot0,\ 1\cdot0.30-0\cdot0,\ 0\cdot0-0\cdot0.30]^T
=[0,0.30,0]^T.
\]
所以 \(J_i=[0,0.30,0,0,0,1]^T\)。乘 \(\dot q_i=0.2\) rad/s，得到 +y 的 0.06 m/s 和 +z 的 0.2 rad/s。0.30 是几何力臂系数，1 是该关节对绕轴角速度的单位影响。

回到第 2.2 节二连杆，\(r_1=[0,0.50,0],r_2=[0,0.20,0]\)：
\[
[0,0,1]\times[0,0.50,0]=[-0.50,0,0],\quad
[0,0,1]\times[0,0.20,0]=[-0.20,0,0].
\]
于是
\[
J=\begin{bmatrix}
-0.50&-0.20\\0&0\\0&0\\0&0\\0&0\\1&1
\end{bmatrix}.
\]
\(\dot q=[0.2,0.1]^T\) 时，TCP 线速度为 \([-0.12,0,0]\) m/s，角速度为 \([0,0,0.3]\) rad/s。两关节共同影响位置和朝向，没有“一个只管位置、另一个只管朝向”的天然分工。

移动关节的几何列是 \([a_i;0]\)，不按转动关节公式计算。某关节若不是 TCP 的祖先，其对该 TCP 的列为零。有限差分可以在电脑内变 q 后重新 FK 检查导数；这与实体试动不同，也不是计算 J 的必需步骤。

### 3.2 七关节与六维任务：冗余来自哪里

七个转动关节控制单 TCP 时，\(J\in\mathbb R^{6\times7}\)。若秩为 6，至少有一维关节速度方向 z 满足 Jz=0：在瞬时一阶近似下，它能改变关节姿势却不改变 TCP 速度。它不是任意大幅运动都不影响末端，持续运动仍需更新 J。

多个任务共享整个模型的同一组速度/小步。例如真正七自由度模型中，两个六维 FrameTask 加七维 PostureTask 可叠成 19×7；真实双臂模型还含两侧关节、夹爪等，列数应为 model.nv，不能拿 19×7 当作 P2 的固定尺寸。独立两臂未必共享活动关节，任务不必然互相冲突；模型耦合、冗余、约束和偏好决定是否需要折中。

## 4. MuJoCo 既是仿真库，也能只做几何计算

| 对象或接口 | 输入/保存什么 | 做什么 |
|---|---|---|
| MjModel | 模型结构、关节轴/原点、执行器等 | 机器人的固定数字模型 |
| MjData | qpos、qvel、ctrl 和派生量 | 此刻的状态与计算缓存 |
| mj_forward | 当前模型与状态 | 计算前向动力学及几何等派生量，不积分时间 |
| mj_step | 模型、状态、控制输入 | 按物理模型推进一个仿真时间步 |
| mj_jacBody/mj_jacSite 等 | 当前几何、指定 body/site | 求该点线/角速度对广义速度的影响 |

图形窗口只显示计算结果；不开窗口仍能算 FK/Jacobian。重算派生量不等于机器人已经执行了动作；改 qpos 是直接改模型状态，改 ctrl 是给执行器输入。[MuJoCo 官方 API](https://mujoco.readthedocs.io/en/stable/APIreference/APIfunctions.html#mj-forward)对 forward 与 step 的区别有明确说明（2026-10-12 核验）。

当前 body/site 几何雅可比可以通过 MuJoCo API 取到上三行平移、下三行旋转。它的速度是在该 frame 原点处、沿世界轴表达。若原点不变，仅换为 TCP 局部轴，变换为
\[
J_E=\operatorname{diag}(R_{BE}^T,R_{BE}^T)J_B.
\]
如果同时换运动的参考点，还涉及平移引起的速度耦合，不能只用两块旋转代替完整伴随变换。

## 5. Mink 怎样接 MuJoCo：几何 J 与误差 J 区分

Mink 是基于 MuJoCo 的任务型差分 IK 库。它将 FrameTask 目标、PostureTask 偏好与实际配置的限制组织成 QP，调用 OSQP 等后端；它本身不是电机驱动。

**2026-10-12 核验时的上游 main 为提交 ae6759602593113ed7e5431ac7c65726ea27dc29（提交时间2026-09-30）。以下引用已固定到该提交，不代表历史安装版本：**

- Configuration 从 MuJoCo 的 body/site/geom 雅可比 API 取几何 J，并把世界轴表达换到局部 frame。见 [Configuration 源码](https://raw.githubusercontent.com/kevinzakka/mink/ae6759602593113ed7e5431ac7c65726ea27dc29/src/mink/configuration.py)。
- FrameTask 使用局部 SE(3) 对数误差 \(e=\log(T_{BE}^{-1}T_d)\)，其误差雅可比还包含符号和 Jlog 修正；不是把几何 J 原封不动当“误差对 q 的导数”。见 [FrameTask 源码](https://raw.githubusercontent.com/kevinzakka/mink/ae6759602593113ed7e5431ac7c65726ea27dc29/src/mink/tasks/frame_task.py)。

教学的 \([p_d-p;\operatorname{Log}(R_dR^T)^\vee]\) 清楚分开世界位置和世界旋转，用于理解反馈。Mink 的完整 SE(3) Log 平移部分还与旋转耦合，不保证等于世界位置差，尤其大姿态误差时。二者都能用六维表示，但表达系、误差函数和 J 必须成套使用。不能手工把教学 e 塞进库的任务 J 并沿用未经检查的正负号。

## 6. QP 选的是步长还是速度：API 内外各是什么

### 6.1 两种教学写法都可用，不能混单位

速度型教学为
\[
\min_{\dot q}\sum_i\|W_i(J_i\dot q-V_i)\|^2+\lambda^2\|\dot q\|^2.
\]
步长型教学为
\[
\min_{\Delta q}\sum_i\|W_i(J_i\Delta q-b_i)\|^2+\lambda^2\|\Delta q\|^2.
\]
前者 V 是每秒任务运动，后者 b 是本步任务变化；\(\Delta q=\dot qdt\)。改变量时残差目标、约束和正则项的数值尺度也须一致，不能只换变量名字。

### 6.2 当前 Mink 内部先解 Δq，API 再返回 Δq/dt

2026-10-12 阅读的上游 main 中，build_ik 的决策变量是切空间小步 \(\Delta q\)，任务一阶式是
\[
J_{error}\Delta q\approx-\alpha e.
\]
gain \(\alpha\) 是无量纲每步误差消除比例，不等于第 1.2 节的每秒增益 K；简单局部情况下可理解为 \(K\approx\alpha/dt\)。

solve_ik 将 QP 解除以 dt，返回速度 \(v=\Delta q/dt\)；本地项目再调用 integrate_inplace(v,dt)，积分成下一配置。因此不能把返回值当 Δq 再重复除/乘周期。见 [solve_ik](https://raw.githubusercontent.com/kevinzakka/mink/ae6759602593113ed7e5431ac7c65726ea27dc29/src/mink/solve_ik.py)与 [Task 定义](https://raw.githubusercontent.com/kevinzakka/mink/ae6759602593113ed7e5431ac7c65726ea27dc29/src/mink/tasks/task.py)。

这一核验说明当前 API 的两层含义。本项目缺少历史环境的 Mink 版本/提交锁定，不能据此宣称历史内部代码完全相同。复现时需要安装版本或 wheel/源码哈希，再核对这四个接口和 defaults。

## 7. 本地求解器与主脚本：同样求 IK，状态更新不同

### 7.1 独立 XarmIKSolver

构造函数加载 XML；把该实例 gravity 设为零，主要用于 IK/运动学更新，并非实机重力补偿。默认 dt=1/200 s，position_cost=1，orientation_cost=0.5，posture_cost=0.01，FrameTask.lm_damping=0.05，后端 osqp。

solve_step 的源码顺序：

当前 data.qpos 副本 → configuration.update → PostureTask 目标设当前 q → 有目标的左右 FrameTask 设置 SE(3) → solve_ik 返回 vel → integrate_inplace(vel,dt) → 得到 q_result。

当 update_state=True，它直接把 q_result 写入 data.qpos 和 data.ctrl，再 mj_forward。前者是直接更新运动学状态；并未通过 mj_step 证明执行器动态跟上。solve_step 对外返回的是积分后的关节配置，不能和内部 solve_ik 返回速度混为一谈。失败时返回 current_q；没有目标时也返回当前配置。

### 7.2 主遥操脚本

主类的 RateLimiter 配置 200 Hz，dt 取 rate.dt。_solve_and_apply_ik 从当前模拟 qpos 更新 Configuration，设置本周期 Posture 和有目标的 FrameTask，积分后**只把关节目标写 ctrl**。外层 _update_ik 再调用 mj_step。模拟 actual qpos 由物理推进产生，不能当作瞬时等于 q_next。

主入口指向 openarm/scene.xml；所读 openarm/openarm_bimanual.xml 的活动关节 actuator 为 position，后面的 motor 示例被注释。assets/openarm 里另一个副本采用 motor，不能混用。ctrl 单位由实际加载模型决定，不是 MuJoCo 所有场景里都为 rad。

保存的 Python 主入口 xml_path 行尾还有异常文本（zhe'l），当前副本的意图路径可读，但不能声称它已直接运行成功。原始文件未修改；环境/语法与运行证据见[运行入口](../02_源码阅读与运行/03_环境配置与运行入口.md)。

### 7.3 积分与四种时间

仅含普通转动关节的教学例：q=[0.1,0.2] rad，vel=[0.4,-0.2] rad/s，dt=0.005 s，则 \(\Delta q=[0.002,-0.001]\) rad、q_next=[0.102,0.199] rad。含自由/球关节时 nq 与 nv 可能不同，配置含四元数，使用流形积分而非逐元素 q+vel。

| 时间 | 来自哪里 | 能否从 IK dt 自动推出 |
|---|---|---|
| XR 样本间隔 | provider/网络采样 | 不能 |
| IK 积分 dt | 求解器/RateLimiter 配置 | 本地默认 5 ms |
| 物理仿真 h | 实际模型 opt.timestep、覆盖赋值和步进次数 | 不能 |
| 墙钟循环周期/电机内环 | 调度耗时、通信、驱动器 | 不能 |

本地脚本的 200 Hz 限速器并不自动将 MuJoCo opt.timestep 改为 5 ms。外层每轮调用一次 mj_step，也不能不看 h 就说每轮仿真前进 5 ms。配置较小 dt 对局部运动更细，但改变 dt 还会改变速度换算与约束；不保证性能总更好。

## 8. 权重、阻尼、限制和收敛分别负责什么

FrameTask 的 cost 调整位置/朝向残差相对重要性；PostureTask 在本周期取当前 q，倾向抑制不必要变化，不能说全程回固定 home。

全局正则、各任务 LM 阻尼可以并存。lm_damping=0.05 是 API 配置值，不能直接当成教学 \(\lambda=0.05\)；完整求导和数值例见[奇异与阻尼](03_奇异阻尼限位与异常保持.md)。

当前上游 limits=None 默认配置范围约束，空列表关闭；速度和碰撞限制要实际配置。这是 2026-10-12 当前上游核验。项目调用省略 limits 且历史版本未锁定，所以不能声称 P2 已可靠限速/避碰。XML actuator 限幅是另一个层次。

solve_until_converged 同时检查关节变化与末端位置/姿态误差；小 Δq 也可能因为阻尼、限位、不可达或求解失败。到位要看真实残差；异常时保持旧参考也可能让下游继续出力，不能叫自动断电。

## 9. 实机可以怎样复用计算链

实机读编码器得到当前关节角，按关节顺序、零位和方向进入模型，算 FK/Jacobian，再求 IK。可以只让 MuJoCo 做几何而不 mj_step；如果继续用 Mink，需要它依赖的 MuJoCo 模型。也可换 KDL/Pinocchio 等库，使用相应 IK。

执行方式取决于驱动模式：

| 下游模式 | IK 结果如何使用 |
|---|---|
| 位置跟踪 | 积分为 q_next，再由驱动跟位置 |
| 速度跟踪 | 发 qdot；驱动跟速度，外层还要管理边界 |
| 力矩控制 | 另一个控制器根据 q/qdot、参考和动力学求 tau |

求出 qdot 不等于已经求出力矩。ROS 发布关节目标也不等于闭环完成；必须确认下游订阅、模式、单位、编码器回流、超时和故障处理。

## 10. 复习时把每个量说出来

按顺序口述：手柄增量生成目标 T_d → 当前 q 经模型得到 T 与 J → 误差给运动要求 → 多任务 QP 求一组小步 → API 返回速度 → 配置积分得 q_next → 执行器跟踪 → 新反馈重算。

自查：

1. 能否按第 3 节逐数字算出两列 J，而不让实体试转？
2. 0.02 m 乘 2/s 是什么量？六维上下三项各是什么单位？
3. 为什么几何 J、局部 J 和 FrameTask 误差 J 的数字不必相同？
4. 本地 solve_step、上游 solve_ik 各返回什么？
5. 为什么 dt=5 ms 不证明 mj_step 的物理步长或实测 200 Hz？

English reference: “The model computes the current pose and geometric Jacobian from joint feedback. Mink builds frame-consistent task residuals and a differential IK problem. The current upstream solver optimizes a configuration displacement and returns it as a velocity divided by dt; the application then integrates this velocity into a joint reference. I distinguish this reference from the actuator’s actual state.”



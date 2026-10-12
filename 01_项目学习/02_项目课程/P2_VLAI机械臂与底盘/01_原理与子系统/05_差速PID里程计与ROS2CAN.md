# 差速运动学、PID、里程计与 ROS 2/CAN

## 0. 先看这一条闭环

底盘上层给“向前多快、转弯多快”，运动学把要求分成左右轮目标；编码器反馈告诉控制器轮子实际怎样转，速度环修正误差；里程计累积**测得的轮动**估计车走到哪里。ROS 2 和 CAN 负责跨进程/设备传数据，各自不会自动完成运动学、PID 或定位。

本章先给标准模型，再对照本地板端实际路径。教学算例不代表硬件数据；本轮不运行软件测试、不改原始板端源码。[源码地图](../02_源码阅读与运行/01_源码版本与文件地图.md)保存阅读快照，[完整周期](../02_源码阅读与运行/02_一个周期的调用与数据流.md)保存调用链。

## 1. 车体速度怎样分成左右轮速度

约定车体 +x 向前、+y 向左、+z 向上，yaw 逆时针为正。轮距 L 单位 m、轮半径 r 单位 m；左右轮轮缘向前线速度都定义为正：
\[
v_r=v+\frac{\omega L}{2},\qquad
v_l=v-\frac{\omega L}{2},
\quad
\dot\varphi_r=\frac{v_r}{r},\quad
\dot\varphi_l=\frac{v_l}{r}.
\]
v 是车体 m/s，ω 是车体 rad/s，轮线速度除半径才是轮角速度 rad/s。左右电机因安装镜像可能编码器正方向相反，接口层需转成同一个“向前为正”的定义。

反算：
\[
v=\frac{v_r+v_l}{2},\qquad
\omega=\frac{v_r-v_l}{L}.
\]
同速直走；右轮更快时向左转；原地左转可令 \(v_r=-v_l>0\)。这里假设平面刚性几何与无侧滑，不能保证实际车体速度正好等于轮子理论值。

教学例 \(v=0.5\) m/s、\(\omega=1\) rad/s、L=0.4 m、r=0.1 m：
\[
v_r=0.7,\quad v_l=0.3\ {\rm m/s};\qquad
\dot\varphi_r=7,\quad\dot\varphi_l=3\ {\rm rad/s}.
\]
反算平均 0.5、差除轮距为 1，单位和方向都能核对。

## 2. 编码器先换单位，才能进入轮速闭环

若编码器每电机圈 C 个计数、传动比 N 为“电机圈/轮圈”，采样时间 dt，计数变化 Δc，则
\[
\Delta\varphi=\frac{2\pi\Delta c}{CN},\qquad
\widehat{\dot\varphi}=\frac{\Delta\varphi}{dt}.
\]
多倍频后的 C、计数回绕、传动比、左右符号必须匹配实际设备。若反馈是 RPM，应先乘 \(2\pi/60\) 转为 rad/s，并明确反馈是电机轴还是轮轴。

每侧速度环误差
\[
e_k=\dot\varphi_{ref,k}-\widehat{\dot\varphi}_k,
\]
一个离散 PID 教学写法为
\[
I_k=I_{k-1}+e_kdt,\qquad
u_k=K_pe_k+K_iI_k+K_d\frac{e_k-e_{k-1}}{dt}.
\]
u 的单位依输出接口确定，可能是力矩、电流、PWM 或协议量；增益单位也随之确定。目标轮速 7 rad/s、测得 6 rad/s，误差为 +1 rad/s，正向驱动力通常应增大。积分饱和、反馈噪声和实际周期会影响结果；输出限幅后需考虑积分抗饱和。

这段是理想速度环的知识解释。**本地某文件有 PID 初始化，不证明该路径调用了 PID；直接发送目标速度也可能由电机驱动内部做速度环，但必须有驱动模式证据。**

## 3. s=rθ：里程计怎样从轮动累积

轮边缘弧长等于半径乘转角。在纯滚动下，它等于轮子向地面推进的距离。一个周期测得左右轮角变化：
\[
\Delta s_r=r\Delta\varphi_r,\quad
\Delta s_l=r\Delta\varphi_l,\quad
\Delta s=\frac{\Delta s_r+\Delta s_l}{2},\quad
\Delta\psi=\frac{\Delta s_r-\Delta s_l}{L}.
\]
它们是位移与角增量，不是速度。若输入为轮速，先乘实测 dt 得角变化；不能让变量名字或固定比例替代单位推导。

当前航向 ψ、中点积分的教学式为
\[
x_{next}=x+\Delta s\cos(\psi+\Delta\psi/2),\qquad
y_{next}=y+\Delta s\sin(\psi+\Delta\psi/2),\quad
\psi_{next}=\psi+\Delta\psi.
\]
中点是小步近似；连续恒定曲率也可用圆弧精确积分。

### 3.1 逐数字把一周期算完

沿用轮速右 7、左 3 rad/s，假设这次测量 dt=0.1 s：轮角变化分别 0.7、0.3 rad。r=0.1 m，则轮走 0.07、0.03 m；平均车体距离 0.05 m，L=0.4 m 则 yaw 增量 0.10 rad。

若起点 x=y=ψ=0，中点式给
\[
x_{next}=0.05\cos0.05\approx0.04994\ {\rm m},\quad
y_{next}=0.05\sin0.05\approx0.00250\ {\rm m},\quad
\psi_{next}=0.10\ {\rm rad}.
\]
若直接用旧 ψ 只会给 y=0，这说明不同积分近似存在差别。算例没有测量误差，不能用于宣称真实里程计精度。

里程计基于反馈，而非仅积分 cmd_vel 目标。打滑、轮径/轮距误差、编码器尺度和时间误差都会积累；它是相对估计，外部定位/IMU融合是另外的链路。

## 4. ROS 2 到 CAN：每个边界要说清字段和时间

一条完整设计链可以写成：

上层车体速度消息 → 桥接/板端解码 → 运动学分配 → 轮目标/驱动命令 → CAN 下发 → 电机和编码器 → 反馈解码 → 轮速控制与里程计 → 上位状态消息。

ROS 的消息发布成功只证明消息送到软件接口；CAN 发送成功也不证明电机已接受模式或准确执行。需要逐层确认消息类型、单位、左右轮序、CAN ID、编码范围、数据新鲜度和超时策略。

若上位确实发布 odom，还需要时间戳、frame_id/child_frame_id、位姿/速度协方差与坐标约定。odom→base_link 的 TF 应有明确唯一来源，不能让多个节点重复发布。cmd_vel 常见线 x、角 z，但本地函数变量 vy 不能仅凭名字解释成“横向速度”。

## 5. 本地板端到底启用了什么

### 5.1 任务顺序与设备尺度

所读 mini_car_self 是 H723 + EZ_RTOS 分支。chassis_task 选择 PROTECT/REMOTER/AUTO 的 Control_Fun，然后 Chassis_ctrl → chassis_odom_calc → msg_to_Host → task_delay(3)。delay(3) 不证明实测周期为 3 ms；调度单位、其他耗时和里程计触发应分别查。

当前 mini_car_calc(vy,vw) 先给
\[
speed=[4(vy+vw),4(vy-vw)],
\]
再给 \(wheel\_ref=[1.5\,speed_0,-1.5\,speed_1]\)。输入 vy=10、vw=2，得到 [48,32]，再得到 [72,-48]，转 int16 后由 MotoSetSpeed 发送。

这是源码数字尺度，不是标准 SI 差速公式。speed_pos=4、1.5、负号的物理意义，以及 vy/vw 的上位单位都要查标定和协议；不能把 [72,-48] 无依据写成 rad/s。

### 5.2 PID 和里程计的活动调用

chassis_pid_calcu 内 pid_calc 被注释，实际 speed_send=wheel_spd_ref 直接进入 MotoSetSpeed。因此该副本不能证明板端轮速 PID 正在调用，也不能否认电机驱动器可能另有内环。需找型号、模式和固件证据。

里程计路径从 moto.speed 乘固定 ratio 得 ds，约 5 ms 条件触发；反馈字段是速度还是累计量、ratio 是否包含 dt 需看协议。注释称中点积分，也要对照先更新 z 再减半角的实际顺序，不能只凭注释说达到某个积分精度。

### 5.3 通信超时和上位连接仍需证据

AUTO 中 host_online>5000 才归零，但自增只在 <5000；若没有其他更新，正常计数可能停在 5000，使 > 条件不触发。另有 tx_data[8] 声明后在所读段未赋值即发送。它们是静态阅读风险，没有本轮运行复现或修复。

机械臂的 ROS 2 发布代码存在；当前底盘 msg_to_Host 到上位 ROS 2 odom 的桥接、完整部署入口尚未定位。不能把板端发包自动说成 ROS 发布里程计，也不能用另一版平台的配置解释此分支。

## 6. 按症状回到数据链

| 症状 | 能区分原因的记录 |
|---|---|
| 左转变右转 | 车体 ω、左右轮理论目标、接口符号、编码器反馈 |
| 目标速度有了但车不动 | 模式、使能、CAN 发送/回包、驱动状态、反馈速度 |
| 直走却持续偏 | 两侧测量、轮径、限幅、地面滑动与机械差异 |
| 轮速看起来很大 | RPM/rad/s、电机轴/轮轴、N、计数倍频 |
| 停止上位消息仍运动 | 命令年龄、host_online 边界、驱动看门狗 |
| odom 漂移或跳变 | 测得轮增量、时间、回绕、坐标与 TF 来源 |

复习时遮住公式，先从 v/ω 算轮速，再用编码器反馈算 ds/dψ，最后分辨哪一步已在本地活动代码中定位。教学实验见[P2 实验说明](../../../03_代码实验/02_项目实验/P2/README.md)；它演示数学，不证明通信或实机 PID 成果。

English reference: “Differential-drive kinematics maps body velocity into two wheel references. A verified wheel-speed loop would compare encoder feedback with these references, while odometry integrates measured wheel motion. In the local board snapshot the PID call is commented out, and the ROS odometry bridge still needs separate evidence.”


# 综合闭环：估计如何进入控制器

## 1. 这次学习什么

模型是一维质点，不是球形、轮腿或导航机器人。你将看到真实状态（模拟才知道）、传感器读数、估计状态和控制命令如何相互影响。完整代码：[closed_loop_demo.py](closed_loop_demo.py)。依赖Python与NumPy；未运行核对，不把下面预期写成实测。

```mermaid
flowchart LR
  A[模拟真实位置速度] --> B[带噪位置测量]
  B --> C[Kalman预测和更新]
  C --> D[位置速度反馈]
  D --> E[加速度限幅]
  E --> A
```

## 2. 模型、符号与单位

状态 \(x=[p,v]^\mathsf T\)：p为m，v为m/s。输入u是m/s²，dt为s。

\[
A=\begin{bmatrix}1&dt\\0&1\end{bmatrix},\qquad B=\begin{bmatrix}dt^2/2\\dt\end{bmatrix},\qquad x_{k+1}=Ax_k+Bu_k
\]

此模型假设每个采样区间加速度恒定。位置观测H=[1,0]，噪声标准差0.05m，R=0.0025m²。模拟每段额外加速度噪声标准差0.10m/s²，Q=0.10²BBᵀ；这是假设的离散随机输入，不是任意连续白噪声的统一公式。

估计器用实际限幅后的输入预测，避免把未执行的大命令当成真实动作。协方差更新用Joseph形式，详见[Kalman主讲](../../01_通用基础/04_传感器与状态估计/README.md)。

控制量 \(u_{\rm raw}=4(p^*-\hat p)-3\hat v\)。这是教学PD状态反馈，**没有计算LQR增益**。4的单位s⁻²，3的单位s⁻¹。位置目标在1秒从0变1m，速度目标0。

## 3. 手算一周期

假设dt=0.1、真实p=0、v=0、上一实际u=1：下一真实p=0.005m、v=0.1m/s（先忽略噪声）。若估计p=0.2、v=0.1，目标1m，原始控制=4×0.8−3×0.1=2.9m/s²，限幅1后实际1。下周期估计必须用1，不用2.9。

标量位置示意：预测0.2、预测方差0.01、测量0.3、R=0.0025，则K=0.8、创新0.1，修正位置0.28。完整位置速度KF还用交叉协方差修正速度。

## 4. 完整命令

从`申请材料`目录运行，所有中文路径加引号。先按[环境说明](../00_环境与运行/README.md)选择Python；下列`python`须是装有NumPy的解释器。

```powershell
python '.\01_项目学习\03_代码实验\03_综合闭环\closed_loop_demo.py' --out-dir '.\01_项目学习\05_实验与学习记录\02_记录与数据\运行结果\LAB-ALL-01\baseline' --seed 7
python '.\01_项目学习\03_代码实验\03_综合闭环\closed_loop_demo.py' --out-dir '.\01_项目学习\05_实验与学习记录\02_记录与数据\运行结果\LAB-ALL-01\delayed' --seed 7 --measurement-delay-steps 5
python '.\01_项目学习\03_代码实验\03_综合闭环\closed_loop_demo.py' --out-dir '.\01_项目学习\05_实验与学习记录\02_记录与数据\运行结果\LAB-ALL-01\limited' --seed 7 --control-limit 0.2
```

```bash
python '01_项目学习/03_代码实验/03_综合闭环/closed_loop_demo.py' --out-dir '01_项目学习/05_实验与学习记录/02_记录与数据/运行结果/LAB-ALL-01/baseline' --seed 7
python '01_项目学习/03_代码实验/03_综合闭环/closed_loop_demo.py' --out-dir '01_项目学习/05_实验与学习记录/02_记录与数据/运行结果/LAB-ALL-01/delayed' --seed 7 --measurement-delay-steps 5
python '01_项目学习/03_代码实验/03_综合闭环/closed_loop_demo.py' --out-dir '01_项目学习/05_实验与学习记录/02_记录与数据/运行结果/LAB-ALL-01/limited' --seed 7 --control-limit 0.2
```

## 5. 按代码顺序阅读

初始化A/B/H/Q/R与随机数→每段用上一实际输入推进真值和预测→生成本次位置观测→选择当前/延迟观测→创新→增益→状态修正与Joseph协方差→参考→PD→限幅→日志→下一周期。

`run_closed_loop(dt,duration,seed,measurement_delay_steps,control_limit)`返回dict，每列等长ndarray；主入口将它保存CSV并另写parameters.csv。

## 6. 输出与预期观察

closed_loop.csv列：time_s、true_position_m、estimated_position_m、true_velocity_mps、estimated_velocity_mps、reference_position_m、control_raw_mps2、control_applied_mps2、innovation_m。默认8s、dt0.02按端点共401行是由代码循环推算，尚未实际运行确认。

预期：位置测量有噪声但估计结合模型；阶跃后原始命令可超限而实际命令受限；减小限幅通常使上升更慢。比较估计对真值误差与真值对参考误差，二者不同。不承诺某组参数一定无过冲或所有延迟稳定。

## 7. 延迟选项刻意展示错误

5步×0.02s=0.10s。程序把旧位置当“现在的位置”更新当前估计，用来演示时间错误；它**没有延迟补偿**。开始尚无到达测量时创新NaN，不能统计成零。正确工程处理需按时间戳更新历史状态再传播，或采用支持延迟观测的估计器。

## 8. 排错与变式

- ModuleNotFoundError：Python环境不含NumPy，先查解释器，不能随意换原项目环境。
- 输出覆盖：每次用新子目录保留条件与参数。
- 非法dt/时长/延迟/限幅：代码明确ValueError；不默默产生伪结果。
- 改dt后延迟秒数与AB/Q都变化，不是只改循环频率。

练习：只看原始输出会高估执行器能力吗？答案会，必须记录applied。KF是否看到真值？答案没有，真值仅用于模拟评估。PD是否就是LQR？答案不是，增益来源不同。

## 9. 面试解释

“This separate learning model connects noisy observations, Kalman estimation, bounded state feedback and a simulated plant. I log both requested and applied inputs. The delay option intentionally misuses old measurements to demonstrate a timing fault; it is not a delay-compensation algorithm.”

记录入口：[模板](../../05_实验与学习记录/02_记录与数据/01_实验记录模板.md)。本实验未运行、未连接设备、无历史实机证明。


## 逐函数理解入口

从[逐函数阅读指南](逐函数阅读指南.md)开始，对照参数、形状、单位、计算顺序、手算和失败条件，再打开程序。代码状态仍为未运行；C++仍为未编译。

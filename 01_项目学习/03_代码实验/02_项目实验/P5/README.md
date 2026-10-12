# P5 普通电脑教学实验

## 初学者先看

练习分别演示车辆短步运动、带车头方向的障碍搜索，以及只执行第一步的MPC跟踪。车辆、地图和轨迹均为教学构造；这不连接原车，也不证明历史Hybrid A*或MPC实机部署。

先在纸上画预期路线，再对照模型假设和约束解释输出。命令尚未运行核对，本轮依照要求不运行。


## 目的、环境和数据来源

三个脚本构成独立车辆模型、合成地图规划和参考跟踪教学；并未声称这是原机部署。MPC用SciPy；其他NumPy。参考点后轴中心，world+x/y、yaw rad、occupied[row=y,col=x]。

Python≥3.10、NumPy；使用SciPy的脚本在导入处明确标出。环境级别A：本地合成数据，无真实机器人。所有脚本未运行核对。本轮未安装依赖。依赖说明见[环境手册](../../00_环境与运行/README.md)。

## 完整命令

PowerShell，工作目录为申请材料：

~~~powershell
Set-Location -LiteralPath "F:/27fall/申请材料"
python "./01_项目学习/03_代码实验/02_项目实验/P5/bicycle_model.py" --out-dir "./01_项目学习/05_实验与学习记录/输出/P5/bicycle_model"
python "./01_项目学习/03_代码实验/02_项目实验/P5/hybrid_astar.py" --out-dir "./01_项目学习/05_实验与学习记录/输出/P5/hybrid_astar"
python "./01_项目学习/03_代码实验/02_项目实验/P5/mpc_tracking.py" --out-dir "./01_项目学习/05_实验与学习记录/输出/P5/mpc_tracking"
~~~

Bash，先把下列cd路径换成此资料的实际挂载路径；在WSL中通常是/mnt/f/27fall/申请材料：

~~~bash
cd "/mnt/f/27fall/申请材料"
python "./01_项目学习/03_代码实验/02_项目实验/P5/bicycle_model.py" --out-dir "./01_项目学习/05_实验与学习记录/输出/P5/bicycle_model"
python "./01_项目学习/03_代码实验/02_项目实验/P5/hybrid_astar.py" --out-dir "./01_项目学习/05_实验与学习记录/输出/P5/hybrid_astar"
python "./01_项目学习/03_代码实验/02_项目实验/P5/mpc_tracking.py" --out-dir "./01_项目学习/05_实验与学习记录/输出/P5/mpc_tracking"
~~~

若python未指向已配置环境，请用解释器完整路径替代；PowerShell调用路径用&，Bash直接用引号路径。随机实验加--seed 7。输出目录由参数选择，脚本不会改原项目参数。

## 按代码走一遍

bicycle_step用本步v/ψ算Euler；Hybrid枚举前后×三舵角，按至少5中间样本检查矩形与格子SAT，连续姿态/72角桶，最多50000展开；MPC以U为变量递推状态，代价Q/R、速度/输入/变化率不等式，求解后查残差再取第一步。MPC参考是模型圆弧，不消费Hybrid路径；规划输出需要另外时间参数化才能接跟踪，完整串联留综合实验说明。

## 输出列、单位与含义

bicycle.csv含case,t(s),x/y(m),ψ(rad),v(m/s),a(m/s²),δ(rad)。path.csv为index/x/y/ψ；status.csv独立记录规划结果；map.csv为占据row/col。mpc_tracking.csv含状态、参考x/y、a/δ/status，无真实测量。

CSV用UTF-8。预期与实际分别写入个人实验记录。

## 预期核对与手算

零舵角直行；L=.5,δ=atan(.5),v=1时yaw_rate=1rad/s。Hybrid输出路径与status，成功需满足位置容差max(.25,2res)、朝向15°，不保证精确终点/全局最优。a_rate2、dt.1使首步Δa≤.2；δ_rate1使Δδ≤.1rad。成功才检查完整约束，失败必须有状态。

## 改参数与异常演示

把goal置于障碍内应invalid_start_or_goal；增大足迹可能无路径；搜索预算耗尽明确返回。MPC初始v超上限或上一输入非法返回失败。正常优化失败采用a_min与上一可行δ制动，速度下界0；故障制动不声称满足正常变化率。无障碍MPC不可称防撞保证。

## 英文面试连接

This is a separate teaching experiment using synthetic data. I use it to explain the mapping and its assumptions; it does not demonstrate historical hardware performance.

概念题：模型表达什么？计算题：复现上面手算；代码题：指出输入检查和输出状态；结果题：说明误差是离散、模型、数值还是实际失败。答案以各脚本的模型、README预期和课程推导为准。

## 求解失败后，下一周期的“上一输入”是什么？

`previous_control` 必须是上一周期实际施加的 `[加速度,转向角]`。求解成功时执行 `plan[0]`；失败时执行保留转向的制动命令，并用 `max(a_min,-v/dt)` 避免一步把速度降到零以下。两条分支之后都将实际 `control` 写回 `previous`，下一次正常输入变化率约束才有正确的起点。

例如上次正常加速度为 +0.2 m/s²，但故障后实际制动为 −1 m/s²，下一周期必须以 −1 为起点。若继续记 +0.2，优化器可能认为指令只小幅变化，真实执行器却收到很大的跳变。故障制动本身可能违反正常变化率限制；这里已明确记录故障状态，不能宣称故障路径仍满足全部正常约束。此说明来自代码阅读，未运行优化器。


## 逐函数理解入口

从[逐函数阅读指南](逐函数阅读指南.md)开始，对照参数、形状、单位、计算顺序、手算和失败条件，再打开程序。代码状态仍为未运行；C++仍为未编译。

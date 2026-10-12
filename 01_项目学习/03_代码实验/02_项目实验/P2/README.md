# P2 普通电脑教学实验

## 初学者先看

这几项练习分别模拟手柄位移到末端目标、手臂关节速度到末端进展、重力与底盘速度换算。它们是普通电脑上的独立教学例子，不接VR控制器、电机、真实机械臂或底盘。

先看项目白话总览确定自己在学哪条项目线，再选一项脚本按输入→中间步骤→输出读。命令只是未来的操作说明；程序当前未运行核对，本轮也不运行。


## 目的、环境和数据来源

相对位姿、平面阻尼IK、二杆重力和主从跟踪，全部合成输入/NumPy，无VR设备或电机SDK。

Python≥3.10、NumPy；使用SciPy的脚本在导入处明确标出。环境级别A：本地合成数据，无真实机器人。所有脚本未运行核对。本轮未安装依赖。依赖说明见[环境手册](../../00_环境与运行/README.md)。

## 完整命令

PowerShell，工作目录为申请材料：

~~~powershell
Set-Location -LiteralPath "F:/27fall/申请材料"
python "./01_项目学习/03_代码实验/02_项目实验/P2/relative_pose.py" --out-dir "./01_项目学习/05_实验与学习记录/输出/P2/relative_pose"
python "./01_项目学习/03_代码实验/02_项目实验/P2/damped_ik.py" --out-dir "./01_项目学习/05_实验与学习记录/输出/P2/damped_ik"
python "./01_项目学习/03_代码实验/02_项目实验/P2/leader_follower.py" --out-dir "./01_项目学习/05_实验与学习记录/输出/P2/leader_follower"
~~~

Bash，先把下列cd路径换成此资料的实际挂载路径；在WSL中通常是/mnt/f/27fall/申请材料：

~~~bash
cd "/mnt/f/27fall/申请材料"
python "./01_项目学习/03_代码实验/02_项目实验/P2/relative_pose.py" --out-dir "./01_项目学习/05_实验与学习记录/输出/P2/relative_pose"
python "./01_项目学习/03_代码实验/02_项目实验/P2/damped_ik.py" --out-dir "./01_项目学习/05_实验与学习记录/输出/P2/damped_ik"
python "./01_项目学习/03_代码实验/02_项目实验/P2/leader_follower.py" --out-dir "./01_项目学习/05_实验与学习记录/输出/P2/leader_follower"
~~~

若python未指向已配置环境，请用解释器完整路径替代；PowerShell调用路径用&，Bash直接用引号路径。随机实验加--seed 7。输出目录由参数选择，脚本不会改原项目参数。

## 按代码走一遍

relative_target校验旋转→父系增量→对齐→初始末端；damped_step解析FK/J→误差速度→线性solve→逐关节限速→积分；leader先算g(q)再PD+g，使用教学单位惯量，未包含真实二杆质量耦合。

## 输出列、单位与含义

relative_pose为目标m与旋转矩阵；damped_ik为λ、t(s)、q(rad)、末端m、误差m、σ(m/rad)；leader_follower为t、主从q、g与τ(N·m)；differential为线速m/s、角速rad/s。

CSV用UTF-8。预期与实际分别写入个人实验记录。

## 预期核对与手算

相对目标从(.3,0,.4)到(.35,0,.4)，朝向转90°；不动保持起点。水平二杆g=[19.62,4.905]N·m。差速示例right7/left3rad/s。λ增大通常减弱奇异速度但增加跟踪残差，实际曲线待运行。

## 改参数与异常演示

把目标移到(3,0)观察不可达残差；改λ/.dt/速度上限，不把clipping称QP。R_alignment镜像矩阵应报错，scale≤0报错。q单位rad，位置m、质量kg；参考变快时看从臂延迟与矩饱和。

## 英文面试连接

This is a separate teaching experiment using synthetic data. I use it to explain the mapping and its assumptions; it does not demonstrate historical hardware performance.

概念题：模型表达什么？计算题：复现上面手算；代码题：指出输入检查和输出状态；结果题：说明误差是离散、模型、数值还是实际失败。答案以各脚本的模型、README预期和课程推导为准。


## 逐函数理解入口

从[逐函数阅读指南](逐函数阅读指南.md)开始，对照参数、形状、单位、计算顺序、手算和失败条件，再打开程序。代码状态仍为未运行；C++仍为未编译。

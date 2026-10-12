# P1 三组教学实验

## 初学者先看

这里的三个脚本分别把三件抽象事变成可观察数字：球怎样变成三轮速度、简化的倒立摆如何比较反馈、手臂移动怎样改变质心和重力矩。它们使用教学尺寸和合成轨迹，不连接P1机器人，也不证明实机效果。

学习时先口头预测方向，再阅读每个变量和CSV列；若以后实际运行，必须另记运行环境与真实结果。按你的要求，本轮不运行这些命令。


**未运行核对**。环境A：几何/CoM需Python+NumPy，balance_compare另需SciPy（当前盘点未装）。全部新合成教学参数/轨迹，无硬件、无原机日志。脚本不改原始model_params。

## 完整命令

从申请材料目录PowerShell：

```powershell
python '.\01_项目学习\03_代码实验\02_项目实验\P1\ball_wheel_mapping.py' --out-dir '.\01_项目学习\05_实验与学习记录\02_记录与数据\运行结果\LAB-P1-01' --latitude-deg 45
python '.\01_项目学习\03_代码实验\02_项目实验\P1\balance_compare.py' --out-dir '.\01_项目学习\05_实验与学习记录\02_记录与数据\运行结果\LAB-P1-02' --torque-limit 5
python '.\01_项目学习\03_代码实验\02_项目实验\P1\com_feedforward.py' --out-dir '.\01_项目学习\05_实验与学习记录\02_记录与数据\运行结果\LAB-P1-03'
```

Bash：

```bash
python '01_项目学习/03_代码实验/02_项目实验/P1/ball_wheel_mapping.py' --out-dir '01_项目学习/05_实验与学习记录/02_记录与数据/运行结果/LAB-P1-01' --latitude-deg 45
python '01_项目学习/03_代码实验/02_项目实验/P1/balance_compare.py' --out-dir '01_项目学习/05_实验与学习记录/02_记录与数据/运行结果/LAB-P1-02' --torque-limit 5
python '01_项目学习/03_代码实验/02_项目实验/P1/com_feedforward.py' --out-dir '01_项目学习/05_实验与学习记录/02_记录与数据/运行结果/LAB-P1-03'
```

## 1. 球轮映射怎么读

ball_wheel_matrix采用实际源码的符号/方位结构，教学半径.12/.06、纬度45°；先degree转rad，再堆每轮投影行。单位角速输入x轴预期[-1.414214,.707107,.707107]轮角速；z轴三轮均+1.414214。solve回到原球角速，记录数值残差。

输出ball_wheels.csv列名明确球/轮rad/s与往返误差。latitude=0或90映射降秩，明确报错。半径非正拒绝。练习改纬度40°与半径比，不能把变化称实机几何已校准。

## 2. 平衡模型怎么读

linear_balance_model沿源码的A11/A12/A22/Δ推连续A/B，状态[x,x_dot,theta,theta_dot]，输入等效τ N·m。TEACHING_PARAMS集中声明合成质量/惯量/长度，非原机参数。

continuous_are求P，K=R⁻¹BᵀP；另一条PD输入明确为.6x+v+20theta+5theta_dot，不是完整原机PID级联。两者同初态theta=.03、dt=.002s、限幅±5，并在1—1.1s加入.1N·m扰动。

输出lqr.csv/pd.csv含时间、四状态、原始/实际力矩与模型范围状态。若|theta|>.4停止并标model_range_exceeded，不把小角度模型外数据当真实跌倒预测。预期比较位置/倾角峰值、恢复、饱和；具体数值待运行记录，不宣称LQR必胜或实机改善。

练习：降低torque-limit，增加初态倾角，观察模型/限幅局限；改变质量与高度须重新求K。SciPy缺失会失败，先建立环境；参数/Δ无效明确拒绝。

## 3. CoM与前馈怎么读

combined_com每部件质量乘同系位置后相加除总质量。机身8kg与双臂各1kg，两臂前伸.3m预期CoM=[.06,0,.52]m，重力pitch矩+5.886N·m，反向补偿-5.886。世界x前、y左、z上，moment=com×[0,0,-mg]，不直接照搬原节点变量tau缩放。

com.csv给时间、CoM、重力与补偿roll/pitch力矩，反向补偿只是静态模型需求；没有完整执行器/身体仿真，不能据此写前馈实机姿态误差降低。固定合成轨迹不调用真实机械臂。

练习：左右臂一前一后，x偏移相消；只有一边横移引入roll；质量总和≤0拒绝。所有结果记录命令、参数、来源与实际输出。

面试连接：[P1课程](../../../02_项目课程/P1_AIRS球形机器人/README.md)。重点解释geometry mapping、model assumptions、feedforward/feedback与分析/部署边界。

## 为什么这里用solve_continuous_are？

这里先针对连续模型 `x_dot=A*x+B*u` 设计LQR，再以dt作数值模拟。P求自连续Riccati方程，`K=solve(R,B.T@P)`对应 `R⁻¹BᵀP`。公式来源与手算见[连续LQR详解第7节](../../../01_通用基础/05_控制与优化/06_LQR二次代价与反馈推导.md)。它与基础实验的离散LQR公式不同；若改变部署采样周期，还需检查离散化和采样保持影响。SciPy当前未安装，未计算运行结果。

## 专门的四状态 LQR 实操

若要亲自完成完整的模型、CARE/DARE、采样、力矩限幅、Q/R 对照、噪声/延迟和图表实验，按[P1 四状态 LQR 仿真实验操作手册](../../../02_项目课程/P1_AIRS球形机器人/03_实验_故障与验证/03_LQR四状态仿真实验操作手册.md)操作。配套程序是[lqr_four_state_sim.py](lqr_four_state_sim.py)，独立依赖见[requirements-lqr.txt](requirements-lqr.txt)。它复制当前源码配置中的模型参数到脚本常量，不读取或改写原始 YAML；结果写入用户指定目录。程序尚未运行核对。


## 逐函数理解入口

从[逐函数阅读指南](逐函数阅读指南.md)开始，对照参数、形状、单位、计算顺序、手算和失败条件，再打开程序。代码状态仍为未运行；C++仍为未编译。

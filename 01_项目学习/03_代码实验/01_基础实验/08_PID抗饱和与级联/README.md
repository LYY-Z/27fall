# LAB-F5-01 PID抗饱和与级联

环境A：Python/NumPy，人工一阶电机与水平双积分车模型。**未运行核对**，无实机参数。积分状态统一为输出单位Iu，D用负测量变化率。

从申请材料目录：

```powershell
python '.\01_项目学习\03_代码实验\01_基础实验\08_PID抗饱和与级联\lab.py' --out-dir '.\01_项目学习\05_实验与学习记录\02_记录与数据\运行结果\LAB-F5-01' --delay-steps 0
```

Bash：`python '01_项目学习/03_代码实验/01_基础实验/08_PID抗饱和与级联/lab.py' --out-dir '01_项目学习/05_实验与学习记录/02_记录与数据/运行结果/LAB-F5-01' --delay-steps 0`。

## 按函数理解

`pid_step`先raw=kp*e+Iu-kd*ydot，再clip，再积分ki*e+kaw*(实际-原始)。手算e=2,kp=2纯P得4；e=3,kp=4原始12限5得到5，ki=1,kaw=2,dt=.1的下一Iu=-1.1。输出顺序为(applied,integral_next,raw)。角度例最短误差-2°。

windup示例一阶模型v̇=(-v+u)/.5，u限±1，前5s目标3不可达，后5s目标0。比较kaw=0与2在降目标后的恢复、积分与饱和时间，不仅比较首次上升速度。v、u在此归一化教学单位。

cascade外环每5×.01=.05s计算位置→限±.6m/s速度参考，内环每.01s速度误差→限±2m/s²加速度。用当前实际加速度按恒加速更新位置速度。delay_steps表示状态反馈延迟多少内环步，本例未实现历史回溯补偿。

输出`no_antiwindup.csv`与`back_calculation.csv`列为时间、参考、速度、原始/实际输出、积分输出；`cascade.csv`列名直接标m、m/s、m/s²。教学设定频率不是实际项目实测频率。

## 改参数与排错

delay_steps改10即100ms，再改50观察恢复与振荡；用不同输出目录避免覆盖记录。修改OUTER_KP增大外环要求，再观察限幅与内环跟踪。高运行频率不能抵消过快外环/延迟。关闭ki/kaw看静态偏差/恢复。

dt≤0、上下限颠倒拒绝；输入NaN拒绝。不要将本例D当误差微分，目标变化时不同；噪声实验可在测量加入固定seed噪声并另加D滤波。本程序无完整电流、摩擦与重力模型。

面试：“I measure overshoot, settling, saturation duration and recovery, and I distinguish inner-loop bandwidth from task update frequency.” 见[抗饱和](../../../01_通用基础/05_控制与优化/03_限幅抗饱和微分与角度误差.md)与[级联](../../../01_通用基础/05_控制与优化/04_级联前馈与多速率.md)。


## 逐函数理解入口

从[逐函数阅读指南](逐函数阅读指南.md)开始，对照参数、形状、单位、计算顺序、手算和失败条件，再打开程序。代码状态仍为未运行；C++仍为未编译。

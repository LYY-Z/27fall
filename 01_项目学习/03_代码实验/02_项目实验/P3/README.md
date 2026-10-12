# P3 普通电脑教学实验

## 初学者先看

练习把云台跨角度边界、发射轮转速恢复和四个麦轮共同分配命令变成可观察数据。电机、弹丸和裁判系统都是简化或合成的，没有接真实硬件，也不能当比赛成绩。

看每个CSV之前，先判断角度单位、轮速单位和电机输出代表什么。源码实际用的控制器版本请回P3章节核对；本轮不运行练习。


## 目的、环境和数据来源

云台rad教学、归一化摩擦轮速、X型麦轮合成参数；与源degree/RPM/电流尺度分开。NumPy，无发射机构动作。

Python≥3.10、NumPy；使用SciPy的脚本在导入处明确标出。环境级别A：本地合成数据，无真实机器人。所有脚本未运行核对。本轮未安装依赖。依赖说明见[环境手册](../../00_环境与运行/README.md)。

## 完整命令

PowerShell，工作目录为申请材料：

~~~powershell
Set-Location -LiteralPath "F:/27fall/申请材料"
python "./01_项目学习/03_代码实验/02_项目实验/P3/gimbal_cascade.py" --out-dir "./01_项目学习/05_实验与学习记录/输出/P3/gimbal_cascade"
python "./01_项目学习/03_代码实验/02_项目实验/P3/launcher_control.py" --out-dir "./01_项目学习/05_实验与学习记录/输出/P3/launcher_control"
python "./01_项目学习/03_代码实验/02_项目实验/P3/mecanum_power.py" --out-dir "./01_项目学习/05_实验与学习记录/输出/P3/mecanum_power"
~~~

Bash，先把下列cd路径换成此资料的实际挂载路径；在WSL中通常是/mnt/f/27fall/申请材料：

~~~bash
cd "/mnt/f/27fall/申请材料"
python "./01_项目学习/03_代码实验/02_项目实验/P3/gimbal_cascade.py" --out-dir "./01_项目学习/05_实验与学习记录/输出/P3/gimbal_cascade"
python "./01_项目学习/03_代码实验/02_项目实验/P3/launcher_control.py" --out-dir "./01_项目学习/05_实验与学习记录/输出/P3/launcher_control"
python "./01_项目学习/03_代码实验/02_项目实验/P3/mecanum_power.py" --out-dir "./01_项目学习/05_实验与学习记录/输出/P3/mecanum_power"
~~~

若python未指向已配置环境，请用解释器完整路径替代；PowerShell调用路径用&，Bash直接用引号路径。随机实验加--seed 7。输出目录由参数选择，脚本不会改原项目参数。

## 按代码走一遍

gimbal外角环→速度参考→矩→惯量.2/阻尼.1；launcher同plant与负载对照PI/边界SMC；mecanum几何A→四轮→P=.2||ω||²→同scale。

## 输出列、单位与含义

gimbal：t(s)、目标/角/误差rad、速度rad/s、矩N·m；launcher：归一化速度、输出、负载，不标成RPM/安培；mecanum：轮序、rad/s、scale、教学预测W。

CSV用UTF-8。预期与实际分别写入个人实验记录。

## 预期核对与手算

跨界误差-2°=-.034907rad；麦轮raw=[1,19,11,9]rad/s，平方和564，教学P112.8W，limit25，scale≈.47078；缩放后模型25W。控制响应与SMC抖动需运行记录，未作性能结论。

## 改参数与异常演示

增加gyro噪声或减内环增益观察跟踪；ε=.01/.2/.5看边界效果；power_limit0全部零，负值报错。独立裁剪轮速与统一比例比较body方向；将目标替换斜坡可观察参考冲击。

## 英文面试连接

This is a separate teaching experiment using synthetic data. I use it to explain the mapping and its assumptions; it does not demonstrate historical hardware performance.

概念题：模型表达什么？计算题：复现上面手算；代码题：指出输入检查和输出状态；结果题：说明误差是离散、模型、数值还是实际失败。答案以各脚本的模型、README预期和课程推导为准。

## 轮速SMC怎样对应教学模型？

`launcher_control.py` 使用 T=0.15 s 的一阶模型 `T*v_dot=u-v-load`，固定目标 r=1。定义 `e=r-v`，滑动面选 `s=e`，控制律为 `u=v+T*k*sat(e/phi)`；代入得到 `e_dot=-k*sat(e/phi)+load/T`。这里函数的 `rate` 参数就是测得轮速 v，不是误差导数。k=5、phi=0.2；外部统一限制 u∈[−5,5]。

手算 v=0.9、e=0.1：sat=0.5，u=1.275；无负载时 v_dot=2.5、e_dot=−2.5。完整推导和扰动/边界层条件见[滑模教材](../../../01_通用基础/05_控制与优化/12_滑模控制与控制方法比较.md)。PI与该控制器使用同一教学对象和负载，但参数未调优，不能据此预先宣称某种方法更好。均未运行核对；原项目SMC方程需另读源码。


## 逐函数理解入口

从[逐函数阅读指南](逐函数阅读指南.md)开始，对照参数、形状、单位、计算顺序、手算和失败条件，再打开程序。代码状态仍为未运行；C++仍为未编译。

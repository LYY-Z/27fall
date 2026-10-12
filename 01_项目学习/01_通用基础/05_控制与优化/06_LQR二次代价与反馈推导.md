# 06 LQR二次代价与反馈推导

先修：[05_状态空间AB与离散化](05_状态空间AB与离散化.md)、[二次型](../01_数学与物理基础/09_特征值二次型与稳定性.md)。项目：P1、P7。目标：从模型到成本、P和K逐步手算。实验：[LQR](../../03_代码实验/01_基础实验/09_LQR与Riccati/README.md)。

## 1. 为何Qx不够表示“扣分”

优化要比较两个动作哪个总成本小，需要一个标量。x形状n、Q n×n，Qx仍n维向量，没有单一总分。xᵀQx为1×n乘n×n乘n×1，得到一个数。

若Q=diag(q₁,q₂)，成本q₁x₁²+q₂x₂²。平方使正负误差都扣分，大偏离扣更多；单位/量级不同应选参考尺度或有量纲权重，不能把米与弧度未经说明混加。

手算x=[.5,.2]，Q=diag(4,1)，Qx=[2,.2]只是加权状态；xᵀQx=.5×2+.2×.2=1.04。非对角权重可编码耦合，要求Q对称半正定保证不出现负惩罚。

## 2. 全部未来一起评分

离散系统x_next=Ax+Bu，代价Σ(xᵀQx+uᵀRu)。Q≥0惩罚状态偏离，R>0惩罚输入。u大可能使误差变小却花很多控制量；u太小可能省动作却让未来误差大。

LQR名字：Linear模型、Quadratic代价、Regulator调节到平衡误差0。它的R不是Kalman传感器噪声，K也不是Kalman融合增益。

## 3. 单步完整展开看到负反馈

模型x_next=x+u，当前x固定，下一状态成本4(x+u)²、输入成本u²：

J=4x²+8xu+5u²。对u求导8x+10u=0，得u=-.8x。二阶导10>0说明最小。x=.5则u=-.4，下一x=.1，成本4×.01+.16=.20；不动u=0成本1，大动作u=-.5成本.25。最佳折中不是直接完全清零。

把R改9，u=-4/(4+9)x≈-.153846（x=.5时），动作更保守。这是一步例，不能把该-.8当完整无限时域K。

## 4. 矩阵负反馈从最小化得来

假设下一状态以后最优成本为V(x_next)=x_nextᵀP x_next。本次成本：xᵀQx+uᵀRu+(Ax+Bu)ᵀP(Ax+Bu)。

P对称，展开与u相关部分为uᵀ(R+BᵀPB)u+2uᵀBᵀPAx。令S=R+BᵀPB，N=BᵀPA。对u的梯度2Su+2Nx=0，得u=-S⁻¹Nx=-Kx。

K形状m×n，u形状m。负号来自优化的代数结果；不表示K每个元素都正，也不表示每个电机直接“朝反方向”，实际B和坐标决定动作。

## 5. 实际使用和局限

定义误差x=actual-target，完整输入u_actual=u* -Kδx；目标轨迹不一定是平衡点，需前馈/跟踪模型。LQR状态反馈需要当前状态，估计器可供x̂，但估计误差/延迟影响实机。

无约束LQR不自动限制输入；clip以后原最优性与线性稳定分析不直接适用。Q增大某项常倾向更关心该状态，但各状态耦合时不能宣称每个增益单调变化。

## 6. 实验、英文与练习

[LQR代码](../../03_代码实验/01_基础实验/09_LQR与Riccati/README.md)提供P/K计算与输出限幅日志。失败：代价不正；状态不是误差；输入单位与B不一致；拿通用K当实机K。

“LQR minimizes a scalar quadratic cost over future state error and control effort. The linear model and quadratic value function make the optimal unconstrained input a linear state feedback.”

追问：Why a scalar cost? It provides a single quantity to minimize and compare control sequences.

1. 概念：Qx是总分吗？答：向量，不是标量。
2. 计算：x=-.5的一步例u？答：+.4，代价与+.5例相同。
3. 代码：K shape (1,2)、x shape(2,)结果？答：u shape(1,)，用于一个输入。
4. 解释：输出超限说明LQR计算错吗？答：可能只是无约束最优输入不可执行，需约束设计/能力检查。

下一章：[07_未来代价P与Riccati逐步计算](07_未来代价P与Riccati逐步计算.md)。

## 7. 为什么P1、P7教学脚本使用另一种LQR公式？

上文是**离散时间**模型：一次更新之后到下一次更新。P1、P7教学脚本先设计**连续时间**LQR，再以小时间步模拟。两种模型、成本和增益公式必须配套。

### 7.1 连续模型与连续成本

设 \(\dot x=A_cx+B_cu\)。这里点表示每秒变化，A_c、B_c由连续运动方程得来。对未来所有时间评分：

\[J=\int_0^{\infty}(x(t)^\mathsf TQ_cx(t)+u(t)^\mathsf TR_cu(t))\,dt.\]

积分把每一小段时间的代价相加；Q_c、R_c给单位时间的成本加权。离散求和则对每一步评分，因此不能不经处理地把两者的权重当成同一意义。

### 7.2 极短时间内：现在的代价加剩下的代价

设最优未来总代价 \(V(x)=x^\mathsf TP_cx\)。考虑很小的时间 h：

\[V(x)\approx\min_u\{h(x^\mathsf TQ_cx+u^\mathsf TR_cu)+V(x+h(A_cx+B_cu))\}.\]

它说：从现在控制到很短一会儿，先付这段成本，再付新状态之后的最优成本。对后一项作一阶展开：\(V(x+h\dot x)\approx V(x)+h\nabla V(x)^\mathsf T\dot x\)。两边抵消 V(x)，除 h，取 h→0，得到

\[0=\min_u\{x^\mathsf TQ_cx+u^\mathsf TR_cu+\nabla V(x)^\mathsf T(A_cx+B_cu)\}.\]

P_c对称，所以 \(\nabla V=2P_cx\)。与 u 有关的项是 \(u^\mathsf TR_cu+2u^\mathsf TB_c^\mathsf TP_cx\)。对 u 求导为零：

\[2R_cu+2B_c^\mathsf TP_cx=0
\quad\Rightarrow\quad
\boxed{u=-K_cx,\qquad K_c=R_c^{-1}B_c^\mathsf TP_c}.\]

没有离散公式中的 \(B^\mathsf TPB\) 项，因为本次变化是无穷小的：展开中的二阶 h² 项在除 h、取极限后消失。

### 7.3 P_c怎么求？连续Riccati方程

把最佳 u 代回上式，把 x 的二次项收在一起：

\[0=x^\mathsf T\big(Q_c+A_c^\mathsf TP_c+P_cA_c-P_cB_cR_c^{-1}B_c^\mathsf TP_c\big)x.\]

这必须对所有状态 x 成立，括号又是对称矩阵，所以括号本身为零：

\[\boxed{A_c^\mathsf TP_c+P_cA_c-P_cB_cR_c^{-1}B_c^\mathsf TP_c+Q_c=0}.\]

这叫连续代数Riccati方程（CARE）。不是把离散递推中的下标删掉。软件求解后，还应看闭环 \(A_c-B_cK_c\) 是否稳定；无限时域的标准结论需要可稳定性、可检测性及适当的Q/R条件。

### 7.4 一个从头手算的例子

只有一个误差，\(\dot x=u\)，所以 A_c=0、B_c=1。取Q_c=4、R_c=1，CARE变成 \(-P_c^2+4=0\)。根有 ±2，选择使闭环稳定且代价非负的 P_c=2；K_c=2，u=−2x。

若 x(0)=0.5，初始输入 u(0)=−1；之后 x(t)=0.5e^(−2t)，u(t)=−e^(−2t)。代价密度为 \(4x(t)^2+u(t)^2=2e^{-4t}\)，积分为 2/4=0.5；也等于 \(V(0.5)=2×0.5^2=0.5\)。因此 P_c是未来代价的系数，不是一个凭空指定的增益。

### 7.5 与离散公式逐项区分

|项目|连续LQR|离散LQR|
|---|---|---|
|模型|x_dot=A_c x+B_c u|x_next=A_d x+B_d u|
|成本|对时间积分|对控制步骤求和|
|求P|连续代数Riccati方程|离散代数Riccati方程|
|求K|R_c⁻¹B_cᵀP_c|(R_d+B_dᵀP_dB_d)⁻¹B_dᵀP_dA_d|
|SciPy函数|solve_continuous_are|solve_discrete_are|

P1的 `balance_compare.py` 与P7的 `lqr_balance.py` 调用 `solve_continuous_are`，然后求 `K=solve(R,B.T@P)`，即通过解线性方程计算 R⁻¹BᵀP，避免手写逆。脚本用离散时间步更新连续模型，是数值模拟；这不等于已经针对该采样周期设计了离散最优控制器。若用于采样系统，需要离散化模型和成本并重新设计，或分析采样保持带来的影响。

本节依据[SciPy官方CARE定义](https://docs.scipy.org/doc/scipy/reference/generated/scipy.linalg.solve_continuous_are.html)，核对日期2026-10-02。教学脚本未运行，P1/P7历史实机采用何种设计仍按各项目版本证据解释。

英文表达："My teaching example solves the continuous-time Riccati equation. I distinguish continuous gain design from numerical simulation at a fixed sample interval."

## 精读补充：把中间步骤讲清楚

### A. 用三个候选动作理解最小化

固定x=.5，J=4(.5+u)²+u²。u=0：J=1；u=−.5：J=.25；u=−.4：J=.20。把误差一步清零并非最低代价，因为动作也扣分。导数让你找到所有连续候选中的最低点，而不只比较三个样本。

Qx=[2,.2]不能直接判断“比另一个向量更小”，两分量可能一大一小。xᵀQx把偏好转成单个数。Q不是传感器的准确程度，修改Q不会改传感器噪声。

### B. 负号并不保证每个增益为正

若模型x_next=x−u，正u会减小x，同样优化得到u=+.8x。统一写u=−Kx，此时K=−.8。负号是标准反馈表达的代数形式，真实方向由B和状态定义决定。

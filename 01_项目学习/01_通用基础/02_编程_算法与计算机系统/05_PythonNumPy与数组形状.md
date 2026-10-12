# 05 PythonNumPy与数组形状

先修：[04_图搜索动态规划与算法分析](04_图搜索动态规划与算法分析.md)。项目：P1、P2、P5、P7。实验：[数据结构与状态同步](../../03_代码实验/01_基础实验/03_数据结构与状态同步/README.md)。

## 1. 数字正确还不够，形状也必须正确

NumPy一维`(n,)`向量没有显式行/列轴；二维列向量是`(n,1)`。两者在矩阵乘法与广播中的行为不同。机器人实验统一状态`(n,)`、矩阵`(m,n)`，用`@`做矩阵乘法。

```python
import numpy as np
J = np.array([[2.,1.],[0.,1.]])  # (2,2)
qdot = np.array([3.,4.])         # (2,)
velocity = J @ qdot             # (2,)
```

`J*qdot`是逐元素乘法，按列广播，结果(2,2)，不是末端速度。`qdot.T`仍(2,)；需要真正列矩阵可用`qdot[:,None]`。

## 2. 完整手算广播陷阱

`pred=np.array([10,20])`形状(2,)；`obs=np.array([[12],[18]])`形状(2,1)。`obs-pred`扩成：

```
[[12-10,12-20],
 [18-10,18-20]] = [[2,-8],[8,-2]]
```

原本期望创新[2,-2]，却出现4个数，程序不一定报错。先把obs定义为`np.array([12,18])`；若从文件读到列矩阵，用明确的reshape并检查总元素数。

## 3. 复制、切片与类型

`view=a[:2]`通常共享原数组内存，改view也改a；`copy=a[:2].copy()`独立。记录“上一时刻状态”应复制，否则后续原地更新会把历史也改掉。

整数数组不能安全存小数积分结果。`q=np.array([0,0],dtype=float)`才适合q+=qdot*dt。输出单位没有由NumPy自动检查，需要变量名与接口文档保证。

## 4. 求方程比显式求逆更直接

解Ax=b用`np.linalg.solve(A,b)`，长方形用lstsq或pinv，显式inv(A)@b通常增加不必要工作。solve需要非奇异方阵；并非调用没抛异常就数值可靠，还需条件数和残差。

## 5. 实验与排错

所有基础实验共用此形状约定。失败一：广播制造错误矩阵；失败二：视图覆盖历史；失败三：度数输入sin/cos，函数实际期待弧度。看shape、dtype、单位和有限性，再读控制公式。

## 6. 英文与练习答案

“I check array dimensions as part of the interface. Broadcasting can produce a valid calculation with the wrong meaning, so I use consistent one-dimensional state vectors and explicit matrix multiplication.”

追问：What does the at sign mean? It performs matrix multiplication, unlike elementwise multiplication.

1. 概念：(2,)转置变(1,2)吗？答：不会。
2. 计算：J@qdot？答：[10,4]；逐元素乘得[[6,4],[0,4]]。
3. 代码：保存old=q后修改q可靠吗？答：不可靠，old=q.copy()。
4. 解释：创新突然(2,2)怎么办？答：检查测量和预测是否混合(2,1)/(2,)。

下一章：[06_编译链接Git与Linux](06_编译链接Git与Linux.md)。复习时先不用术语解释例子，再复述英文。

## 精读补充：把中间步骤讲清楚

### A. 一个不报错的广播错误怎样进入Kalman？

预测shape=(2,)，测量shape=(2,1)，相减变成(2,2)，会把“第一个测量减第二个预测”也算出来。正确任务是一一对应的两个创新，不是所有组合。

接口可先检查状态、测量、J的精确shape，再转换。不要不加判断地flatten任意数组：例如2×2误差矩阵flatten成4个数，只把错误藏到了下一步。

### B. old_state为什么要copy？

`old=state`让两个名字指向同一数组；`state[0]=3`之后old[0]也变3。`old=state.copy()`才保存旧数值。MPC的上一实际输入、微分的上次误差、记录的时间轨迹都可能因别名误用而失去历史。

### C. 一维向量与二维列向量各自怎样乘？

J shape=(2,3)，qdot=(3,)时结果(2,)；qdot=(3,1)时结果(2,1)。两种都能表示数学映射，但之后的加减也要保持一致。Python列表`[1,2]*2`得到[1,2,1,2]，不是数值向量[2,4]；要先定义NumPy浮点数组再作科学计算。

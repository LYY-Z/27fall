# P4 普通电脑教学实验

## 初学者先看

三个脚本分别模拟水泵状态变化、带时间戳的视觉事件、规则/建议经过执行策略。它们只使用合成输入，不访问真实相机、NPU、水泵、服务器或互联网。

先手工预测给定湿度或事件年龄会发生什么，再看脚本怎样记录原因。源码有证据的阈值与新增教学保护要分开；当前未运行核对，本轮不运行。


## 目的、环境和数据来源

三实验只用Python标准库，无摄像头/网络/LLM。数据是人工序列。阈值引用源56/65作教学，invalid/stale关泵是教学明确策略，非源完备失效保护证据。

Python≥3.10、NumPy；使用SciPy的脚本在导入处明确标出。环境级别A：本地合成数据，无真实机器人。所有脚本未运行核对。本轮未安装依赖。依赖说明见[环境手册](../../00_环境与运行/README.md)。

## 完整命令

PowerShell，工作目录为申请材料：

~~~powershell
Set-Location -LiteralPath "F:/27fall/申请材料"
python "./01_项目学习/03_代码实验/02_项目实验/P4/irrigation_state_machine.py" --out-dir "./01_项目学习/05_实验与学习记录/输出/P4/irrigation_state_machine"
python "./01_项目学习/03_代码实验/02_项目实验/P4/vision_event.py" --out-dir "./01_项目学习/05_实验与学习记录/输出/P4/vision_event"
python "./01_项目学习/03_代码实验/02_项目实验/P4/decision_replay.py" --out-dir "./01_项目学习/05_实验与学习记录/输出/P4/decision_replay"
~~~

Bash，先把下列cd路径换成此资料的实际挂载路径；在WSL中通常是/mnt/f/27fall/申请材料：

~~~bash
cd "/mnt/f/27fall/申请材料"
python "./01_项目学习/03_代码实验/02_项目实验/P4/irrigation_state_machine.py" --out-dir "./01_项目学习/05_实验与学习记录/输出/P4/irrigation_state_machine"
python "./01_项目学习/03_代码实验/02_项目实验/P4/vision_event.py" --out-dir "./01_项目学习/05_实验与学习记录/输出/P4/vision_event"
python "./01_项目学习/03_代码实验/02_项目实验/P4/decision_replay.py" --out-dir "./01_项目学习/05_实验与学习记录/输出/P4/decision_replay"
~~~

若python未指向已配置环境，请用解释器完整路径替代；PowerShell调用路径用&，Bash直接用引号路径。随机实验加--seed 7。输出目录由参数选择，脚本不会改原项目参数。

## 按代码走一遍

irrigation优先manual off→无效传感→manual保持→auto滞回；vision先schema/time再框/conf；decision只产建议，执行仍调用状态机，不用建议绕过模式。

## 输出列、单位与含义

irrigation.csv：序号/mode/湿度教学%/请求/fresh/pump/reason；vision_events.csv：case/通过数量/status；decision_replay.csv：建议字段与独立模拟执行结果，无硬件ACK。

CSV用UTF-8。预期与实际分别写入个人实验记录。

## 预期核对与手算

55/60/64/66/60序列on/on/on/off/off；manual off本步必off；传感过期关泵。now10, timestamp8, maxage1拒绝stale，conf高无效。manual模式下干土建议start但无manual on请求，执行保持off。

## 改参数与异常演示

阈值相等报错，湿度None/NaN/超范围→off；未来视觉时间拒绝；非法box拒绝；conf门槛更高可能空结果。检测schema是教学字段，源class/bbox/timestamp要先适配。

## 英文面试连接

This is a separate teaching experiment using synthetic data. I use it to explain the mapping and its assumptions; it does not demonstrate historical hardware performance.

概念题：模型表达什么？计算题：复现上面手算；代码题：指出输入检查和输出状态；结果题：说明误差是离散、模型、数值还是实际失败。答案以各脚本的模型、README预期和课程推导为准。


## 逐函数理解入口

从[逐函数阅读指南](逐函数阅读指南.md)开始，对照参数、形状、单位、计算顺序、手算和失败条件，再打开程序。代码状态仍为未运行；C++仍为未编译。

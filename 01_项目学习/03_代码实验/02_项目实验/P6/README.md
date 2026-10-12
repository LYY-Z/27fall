# P6 普通电脑教学实验

## 初学者先看

练习用假设备演示能力注册、过期反馈拒绝、重复动作处理和C++适配器接口。它们不访问生产硬件或M-DDS/M-Robots平台，也不证明历史SDK兼容。

先把动作想成有设备名、编号、时间和值的工作单，再追它如何通过检查并得到模拟回执。文中Python/C++命令未运行核对，本轮按要求不运行、不编译。


## 目的、环境和数据来源

Python标准库单进程模拟，所有输入人工；注册默认不可执行，先同步。C++17 Mock接口另见下方编译命令。无M-DDS网络/设备通信，不是平台历史源。

Python≥3.10，两个Python脚本只使用标准库，不依赖NumPy或SciPy。环境级别A：本地合成数据，无真实机器人。所有脚本未运行核对。本轮未安装依赖。平台构建边界见[环境配置与运行入口](../../../02_项目课程/P6_深开鸿KaihongMeta/02_源码阅读与运行/03_环境配置与运行入口.md)。

## 完整命令

PowerShell，工作目录为申请材料：

~~~powershell
Set-Location -LiteralPath "F:/27fall/申请材料"
python "./01_项目学习/03_代码实验/02_项目实验/P6/capability_dispatch.py" --out-dir "./01_项目学习/05_实验与学习记录/输出/P6/capability_dispatch"
python "./01_项目学习/03_代码实验/02_项目实验/P6/freshness_recovery.py" --out-dir "./01_项目学习/05_实验与学习记录/输出/P6/freshness_recovery"
~~~

Bash，先把下列cd路径换成此资料的实际挂载路径；在WSL中通常是/mnt/f/27fall/申请材料：

~~~bash
cd "/mnt/f/27fall/申请材料"
python "./01_项目学习/03_代码实验/02_项目实验/P6/capability_dispatch.py" --out-dir "./01_项目学习/05_实验与学习记录/输出/P6/capability_dispatch"
python "./01_项目学习/03_代码实验/02_项目实验/P6/freshness_recovery.py" --out-dir "./01_项目学习/05_实验与学习记录/输出/P6/freshness_recovery"
~~~

若python未指向已配置环境，请用解释器完整路径替代；PowerShell调用路径用&，Bash直接用引号路径。这两个脚本使用固定合成事件，没有随机数，也没有 `--seed` 参数。输出目录由 `--out-dir` 选择，脚本不会改原始项目参数。

## 按代码走一遍

register保能力/序号/反馈时间/online/执行ID；feedback只接受更大seq且年龄≤1s；dispatch逐层schema/设备/去重/能力/时效/value[-1,1]；C++用unique_ptr持有基类接口，SharedDevice用mutex保护操作与反馈；异步任务按值捕获Command并持有shared_ptr，main显式get完成后再stop。

## 输出列、单位与含义

dispatch.csv：action_id/status/reason/注册/同步状态；recovery.csv：seq/sample/now(s)、反馈/动作状态；adapter.csv：operation/accepted/seq/归一值/online。

CSV用UTF-8。预期与实际分别写入个人实验记录。特别是freshness_recovery：旧序号会拒绝更新，但如果上一份缓存仍未过期，脚本随后提出的动作仍可能被接受；等缓存年龄超过1秒后，动作才因旧状态而拒绝。

## 预期核对与手算

a1第一次executed、第二duplicate；fly/过期/value2拒绝。seq旧不覆盖，反馈过期使动作拒绝，恢复更新新序号/时间再允许动作。C++a1一次成功一次false，a2越界false；async_a3执行归一值.25、序号2，get完成后stop归零、序号3。这是按源码手算，当前未编译/运行。

## 改参数与异常演示

改now超过反馈1s、issued超max_age、能力未知、重复注册；新注册不会直接online。示例不含boot/session与持久日志，重启序号问题不能说已解决。C++演示异步所有权与串行访问；get没有截止时间，也没有取消语义或持久去重。shared_ptr保证对象寿命，mutex才保护状态；另读基础实验的生产者/消费者与join。

## 英文面试连接

This is a separate teaching experiment using synthetic data. I use it to explain the mapping and its assumptions; it does not demonstrate historical hardware performance.

概念题：模型表达什么？计算题：复现上面手算；代码题：指出输入检查和输出状态；结果题：说明误差是离散、模型、数值还是实际失败。答案以各脚本的模型、README预期和课程推导为准。


## C++完整命令（未执行）

PowerShell从申请材料目录，以相对英文输出名减少Windows argv编码差异；源码路径用引号：

~~~powershell
g++ -std=c++17 -Wall -Wextra -pthread "./01_项目学习/03_代码实验/02_项目实验/P6/device_adapter.cpp" -o "./device_adapter_demo.exe"
& "./device_adapter_demo.exe" --out-dir "./p6_cpp_output"
~~~

Bash：

~~~bash
g++ -std=c++17 -Wall -Wextra -pthread "./01_项目学习/03_代码实验/02_项目实验/P6/device_adapter.cpp" -o "./device_adapter_demo"
./device_adapter_demo --out-dir "./p6_cpp_output"
~~~

较旧g++的filesystem可能需要独立库或升级编译器，当前版本未编译核对；不得把编译命令当成功记录。可将输出索引写入个人实验记录，不删除原源码/材料。


## 逐函数理解入口

从[逐函数阅读指南](逐函数阅读指南.md)开始，对照参数、形状、单位、计算顺序、手算和失败条件，再打开程序。代码状态仍为未运行；C++仍为未编译。

# 07 INT8量化RKNN与边缘部署

先修：[06_训练损失梯度与模型评估](06_训练损失梯度与模型评估.md)。相关项目：P4。目标：把本章算法接到输入、输出、手算和工程失败。

## 1. 为什么把浮点换成整数

浮点权重/激活占存储与算力；INT8用有限整数和尺度近似数值，硬件可更有效执行。最简对称量化q=clip(round(x/s),-127,127)，反量化x̂=sq。实际网络可能用非对称zero_point、逐通道尺度和混合精度，不能用一个s代表整个RKNN图。

## 2. 完整手算误差

s=.1,x=.26，x/s=2.6，round得3，反量化.3，误差+.04。无裁剪时舍入误差通常≤s/2=.05。x=13时量化上限127，反量化12.7，误差-.3，超过半scale，因为饱和裁剪。

尺度小分辨细但覆盖范围窄；尺度大覆盖广但误差大。校准数据帮助估计激活范围，应代表真实摄像头、光照、植物和预处理；只用不相关图片不能假定精度保持。

## 3. RKNN链路怎样读

训练/已有模型→导出ONNX等→Toolkit转换与量化→.rknn模型→板端runtime推理→后处理。模型转换与板端推理工具不同，版本/目标芯片/算子支持要兼容。

P4 RK3588模型输入颜色、尺寸、mean/std、量化开关和dataset逐项从转换脚本读；板端模型、librknnrt与预处理一致再解释效果。不因有onnx2rknn.py就认定转换成功或速度提升。

## 4. 来源与实验

[Rockchip官方Toolkit2仓库](https://github.com/airockchip/rknn-toolkit2)为版本/文档入口，查阅2026-10-02；具体依赖按本项目记录核对。本[教学量化实验](../../03_代码实验/01_基础实验/12_搜索图像与协议/README.md)只演示数组INT8，不创建真实.rknn。

失败：校准与部署预处理不一致；模型/runtime不匹配；误把confidence当精度；只测推理算子而忽略摄像头、网络和后处理延迟。比较浮点/INT8须同数据与硬件条件，记录误差和延迟。

## 5. 英文与练习

“Quantization approximates floating-point values with integers and scale factors. Calibration should represent deployment data, and I compare detection quality and end-to-end latency rather than assuming INT8 is always better.”

追问：When does the half-scale error bound fail? When clipping occurs, or when other quantization effects are included.

1. 概念：INT8等于模型只有8个权重？答：每数值用8位整数表示，不是权重个数。
2. 计算：s=.2,x=.46？答：q=2,x̂=.4,error=-.06。
3. 代码：s≤0怎么办？答：拒绝。
4. 解释：变快但漏检多？答：精度/性能权衡，检查校准/尺度/预处理，不能只报告速度。

下一章：[08_Agent状态工具与执行边界](08_Agent状态工具与执行边界.md)。

## 精读补充：把中间步骤讲清楚

### A. 带零点的量化也要先理解尺度

一般q=round(x/s)+z，反量化xhat=s(q−z)。s=.1,z=128,x=.26，q=131，xhat=.3；整数128此时表示真实0，不是128单位。这里是教学非对称例，不代表P4每个张量的真实尺度。

端到端一帧包括采集10ms、预处理5、推理20、后处理5、传输10，总50ms；只测20ms算出50次/s，不等于整个链路端到端50帧/s。流水线吞吐和单帧延迟还不同，必须分别定义。

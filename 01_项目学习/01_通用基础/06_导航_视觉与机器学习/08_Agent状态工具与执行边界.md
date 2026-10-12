# 08 Agent状态工具与执行边界

先修：[07_INT8量化RKNN与边缘部署](07_INT8量化RKNN与边缘部署.md)。相关项目：P4、P6。目标：把本章算法接到输入、输出、手算和工程失败。

## 1. Agent不是把一段自然语言直接送电机

传感器事件进入结构化state；规则或模型生成建议；策略层检查设备能力、阈值、时间、模式和权限；执行层发命令；回执与实际反馈更新状态。语言建议不能自行绕过本地闭环与人工停机。

LangGraph用state、node、edge组织流程：节点计算/调用工具，边决定下一步，状态保存当前信息。节点可以纯规则，也可以调用LLM。循环需终止/预算/故障条件。

## 2. 手算灌溉状态

auto模式，湿度25，启动阈30、停止阈40，pump_off：建议on；湿度35且pump_on：保持on；湿度42：off。manual_off立即优先。湿度传感器过期时，教学策略停泵并报告原因，真实项目按代码检查。

视觉发现病叶并不自动意味着应该浇水，病害与水分是不同变量。旧图像/低置信只可作弱证据，建议不能替代有效湿度与执行规则。

## 3. 工具接口的合同

输入action_id、device_id、capability、value、issued_at、有效期；输出accepted/rejected/executed与reason。JSON可解析不代表语义合法，检查范围、枚举与设备状态。网络内容/模型输出属于数据，不作为系统授权。

重试需幂等ID，异步执行需反馈确认。记录每次依据与状态，有助面试解释why和排错，而非只展示聊天截图。

## 4. 来源、实验与失败

图工作流基础见[LangGraph官方API](https://docs.langchain.com/oss/python/langgraph/graph-api)，查阅2026-10-02；本教材不承诺当前库接口与旧源码完全一致。P4/P6教学回放不调用外部LLM API。

失败：建议直接物理执行；旧状态反复决策；人工off被自动on覆盖；循环重复动作；执行回执误当达到目标。检查state schema、路由、动作ID与日志。

## 5. 英文与练习

“The agent produces structured proposals from state and events. A separate policy and execution layer checks whether an action is valid and confirms its outcome through feedback.”

追问：Why keep a rule-based fast path? Deterministic local conditions can be handled quickly and predictably without waiting for an LLM.

1. 概念：图节点一定LLM吗？答：可纯函数/规则/工具。
2. 计算：湿度35、泵off、阈30/40？答：保持off，滞回保持状态。
3. 代码：manual_off后自动建议on？答：策略层拒绝覆盖。
4. 解释：模型说已浇水等于执行了吗？答：不，需命令与物理反馈。

下一章：[09_学习控制与强化学习入门](09_学习控制与强化学习入门.md)。

## 精读补充：把中间步骤讲清楚

### A. 事件、建议、命令和结果是四个阶段

事件“湿度25”描述测量；建议“应浇水”描述决策；命令“设备A开泵，动作ID42”描述执行请求；结果“继电器已通、流量有效”才反馈执行情况。模型生成一句“已经浇水”不能跳过中间两阶段。

ID42重发要查是否已经执行；新会话的ID42不能误判旧会话相同动作。人工off与过期状态是执行层需检查的条件。P4真实fast path是规则，不能把每次自动动作都说成LLM推理。

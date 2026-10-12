# 07｜香港城市大学（东莞）：MSc in Artificial Intelligence

## 官方项目理解

CityUHK(DG) AI 页面当前显示 2027 申请，培养目标包括使用 AI 工具与技术开发解决方案、设计高质量 AI 系统、并在开发过程中有效协作。[官方 AI 项目页](https://pga.cityu-dg.edu.cn/Artificial-Intelligence)

面试中说 programme 的具体模块前，先从申请系统或最新项目页确认所选课程；这里不把其他学校的 AI 课程套到 CityUHK(DG)。

## 45–60 秒：Why CityUHK(DG) AI?

> I am applying to the MSc in Artificial Intelligence because I have used AI in practical systems and now want stronger foundations in the methods behind it. In my smart-gardening project, I connected YOLOv5 edge inference on an RK3588 board to a LangGraph decision chain and a local irrigation state machine. At Kaihong, I have also worked on a safe execution path for robot tasks. These experiences made me interested in how to turn model outputs into dependable system behaviour. I want to study AI systematically and learn to evaluate models, not only deploy them. My goal is to apply that training to intelligent robot systems in the Greater Bay Area.

## 申请匹配：P4 是主例，P6 是安全/系统例

- P4 说明你做过视觉推理、边缘部署、agent 决策链与设备闭环。
- P6 说明高层任务建议必须经过策略检查、执行和状态回传；不能让 agent 直接越过安全边界操纵机器人。
- P5/P1/P7 作为下游应用例子，说明 AI 组件最终要面对定位误差、物理限制和执行延迟。

## 可能追问与英文答法

### What does the confidence score mean, and what does it not mean?

> A detector’s confidence is a model output associated with a prediction. It is not automatically the probability that the real-world decision is correct under every condition. I would calibrate and evaluate it on representative data, account for distribution changes, and avoid using it as the only safety condition for an actuator.

### Why use a rule-based fast path together with an AI decision chain?

> A learned or agent-based decision can be useful for flexible cases, but some states need a predictable response. A rule-based path can handle defined extreme conditions, while the policy layer checks whether a proposed action is allowed. The two paths still need clear priority, validation and logging; simply adding rules does not prove the system is safe.

### What is INT8 quantization, and what trade-off does it create?

> INT8 quantization represents model values with lower-precision integers instead of the usual floating-point representation. It can reduce memory use and inference cost on supported hardware, but it can also affect accuracy. I would compare the quantized model with the reference model on the same test set and report task metrics and hardware latency, if measured.

### Have you trained YOLOv5 yourself?

Answer only what is supported by the current CV/PS and your records. Safe version if the project work was deployment rather than training:

> My documented contribution focused on building and deploying the inference and application chain. I would not claim a training contribution unless I can identify the dataset, training process and model changes I personally made.

### How would you evaluate a model for a physical robot?

> I would evaluate more than average accuracy. I would include the relevant task metric, confidence calibration, latency, memory use, behaviour under poor or missing observations, and the effect on downstream control. For safety-critical actions, I would test the complete system and retain an independent safety check.

## 建议反问

- What project-based opportunities are available for students to evaluate AI systems in real application settings?
- How does the programme teach model evaluation, deployment and responsible AI alongside model development?
- What collaboration opportunities exist between AI students and robotics or manufacturing teams?

## 事实边界

- 不把 “agent” 说成已自主控制机器人；CV 说的是建议/受限请求与安全执行链。
- 不声称自己训练过大型模型或实现了强化学习，除非能给出数据、训练流程与代码证据。
- 没有实测日志时不要回答推理 FPS、精度提升和系统成功率。

---

回到[学校定制索引](README.md)。

## 面试与项目目标补充

官方学习成果涉及 AI 软件/系统开发、提出解决方案和团队协作；未查到固定面试题目/形式。[MSc AI 官方页](https://pga.cityu-dg.edu.cn/en/artificial-intelligence)。

用 P4 讲数据/模型/部署/设备动作/保护，用 P6 讲接口与协作。练习追问：How did you evaluate the model on the target device? What happens with invalid or stale data? Which task did you personally own? 这些是按项目目标推导的练习题，不是官方题单。

见[核验总表](../06_网络面试信息核验与练习优先级.md)。

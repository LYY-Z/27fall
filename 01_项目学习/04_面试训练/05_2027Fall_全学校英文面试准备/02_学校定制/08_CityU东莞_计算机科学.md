# 08｜香港城市大学（东莞）：MSc in Computer Science

## 官方项目理解与批次核验

官网 CS 项目页的培养目标包括增强软件开发能力，深化 AI、数据科学、信息安全、多媒体等领域知识；预期学习成果提到计算机系统开发、网络/软件/数据工程和团队协作。[MSc CS 官方页](https://pga.cityu-dg.edu.cn/en/computer-science)｜[项目总览](https://pga.cityu-dg.edu.cn/en/programmes)

本次核验到的英文 CS 项目页仍显示 2026 入学日期信息，不能据此确认 2027/28 的招生轮次。面试前核对个人申请系统中的 2027 入学选项和项目名称。

## 45–60 秒：Why this programme?

> I am applying to the MSc in Computer Science because robot development depends on reliable software and data systems as well as algorithms. At Kaihong, I have worked on capability abstraction, command mapping, state synchronization and task dispatch on an OpenHarmony platform. My work on robot control and navigation also made me consider timing, interfaces and data validity, because a software inconsistency can affect physical execution. The programme’s focus on software development, networks, data engineering and computer-science applications matches the foundations I want to strengthen. I hope to apply them to reusable and dependable robotics software.

## CityUHK(DG) CS 与 AI：怎样说明你选 CS

> I see Computer Science as the better fit for the software-platform side of my goal. I want to improve how robot systems represent state, communicate, coordinate tasks and handle failures. AI is relevant to my work, but the central gap I want to address through this application is the engineering foundation that allows algorithms to run reliably across different robots.

如果申请系统实际选的是 AI，不要用这段替代 AI 的动机回答。

## 可能追问与英文答法

### What is one software-engineering problem you encountered?

> One recurring issue is inconsistent state information. Sensor and actuator values can use different timestamps, frames or validity rules. If these are not made explicit, an upper layer may combine values that do not describe the same robot state. I worked on standardizing those fields and on making the state available to downstream control and task layers.

### How do you design for failure?

> I would define the component’s inputs, outputs and error states first. Then I would test missing, delayed, invalid and out-of-range data, and specify what the caller should do in each case. For an actuator, a proposed action should be checked against policy, freshness and hardware limits, and the system should report the resulting state.

### What does good teamwork look like in software development?

> Good teamwork starts with a shared interface and clear ownership. Each person can work on a module, but the team must agree on data types, units, timing, error handling and review expectations. I would integrate early, test with the other modules and make blockers visible instead of waiting until the end.

### How would you measure whether a platform interface is reusable?

> I would look at how much hardware-specific logic remains in the upper layer, whether the interface preserves device limits, and whether the same application logic can work with more than one adapter. I would also test error handling and state consistency. I would not claim reuse simply because two devices share a message type.

## 建议反问

- Which software or data-engineering courses are available to students who want to work on robotics platforms?
- Does the programme offer team projects that involve systems integration or distributed software?
- For the 2027 intake, is the published course list final, and are there project or internship components?

---

回到[学校定制索引](README.md)。

## 面试信息与 CS 方向补充

CityUHK(DG) 官方介绍将 AI、数据科学、信息安全、多媒体等列入 MSc CS 覆盖方向，并强调软件开发与行业研发；未找到固定面试题目/形式。[官方介绍](https://pga.cityu-dg.edu.cn/en/home)。

回答“为什么选 CS 而不只读 AI”时，说清希望补强算法、软件工程、数据/系统和可靠集成，再用 P6 的接口/状态一致性经历举例。练复杂度分析、数据结构、调试、并发和测试，不只复述控制算法名。

见[核验总表](../06_网络面试信息核验与练习优先级.md)。

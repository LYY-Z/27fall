# 03｜香港中文大学（深圳）：MSc in Computer Science

## 官方项目理解

CUHK-Shenzhen SDS 的 2027 招生说明列出 MSc in Computer Science。项目介绍覆盖计算机基础、网络与系统、AI、数据和软件工程等内容。[2027 招生说明](https://sds.cuhk.edu.cn/en/article/2462)｜[MSc CS 项目页](https://sds.cuhk.edu.cn/en/page/2132)

你选择 CS 方向的逻辑不是“我不做机器人了”，而是：机器人一旦进入多传感器、异构设备和分布式协同环境，可靠的软件平台和数据状态同样决定动作是否正确。

## 45–60 秒：Why this school and programme?

> I am applying to the MSc in Computer Science because my robotics work has repeatedly exposed software problems behind physical behaviour. At Kaihong, I have worked on device capabilities, ROS and ROS 2 command mapping, state synchronisation and task dispatch over M-DDS. These tasks made me realize that timestamps, coordinate frames, interfaces and system architecture are not secondary details; they affect whether a robot can act reliably. The programme’s coverage of computer science, networks and systems, AI, data and software engineering matches the foundations I want to strengthen. I hope to apply that training to dependable robot platforms and robotics software in the Greater Bay Area.

## 申请方向的关键区别：AI/Robotics vs Computer Science

被问“你为什么同时申请机器人和 CS 方向”时：

> The two directions address different parts of the same goal. Robotics training helps me understand mechanisms, estimation, planning and control. Computer Science training helps me build reliable software, data and distributed systems that let those algorithms run across platforms. I am not treating the programmes as interchangeable; I am comparing which foundation best fits the role I want to take next.

根据面试学校，回答只谈当前项目，不要把另一所学校的课程表搬过来。

## 技术追问：用 Kaihong 讲一条平台链

### What problem did the capability abstraction solve?

> Robots can expose different sensors and actuators through different low-level interfaces. A capability abstraction provides a common description of what a device can do, while an adapter maps a higher-level ROS or ROS 2 command to the relevant driver. The goal is to reduce hardware-specific assumptions in upper layers. It does not make all devices identical; the adapter and capability contract still have to preserve each device’s limits and semantics.

### Why are timestamps and coordinate frames important?

> A value without a timestamp may be stale, and a position without a frame has no complete spatial meaning. If a controller combines a recent wheel state with an old or differently framed perception result, it can make a wrong decision even when each message is individually valid. I helped standardize state information so that downstream layers could check its frame, time and validity.

### What does M-DDS do in your description?

> In my project description, M-DDS is used for device discovery, capability registration, state synchronization and task dispatch. I would describe the application-level flow I worked on, and I would distinguish that from the middleware’s internal implementation unless I had inspected and modified that layer myself.

### How do you prevent a high-level plan from directly moving an actuator?

> The plan first becomes an action proposal. A policy check validates whether that proposal is allowed in the current state. Only then is it sent for execution, and the resulting state is fed back. This separates proposing an action from authorizing and executing it. I would still need to check freshness, failure handling, permissions and actuator limits at each boundary.

## 可能追问

### Which part did you personally implement?

> My documented work includes a unified capability model, ROS and ROS 2 command mapping, state-management rules, and parts of device discovery and task coordination on OpenHarmony. I would be precise about the modules I owned and separate them from the broader platform and team work.

If asked for a concrete commit or design example, cite only a real change, review or log you can show; do not invent a code artifact.

### How would you test a robot platform interface?

> I would test the interface at several levels: unit tests for message conversion and validation, integration tests with a simulated or mock driver, and hardware tests with recorded timestamps and feedback. I would include invalid, delayed and missing data cases, as well as limit and recovery cases. I would report measured behaviour rather than assuming that a successful build proves reliable execution.

### What would you study next?

> I want stronger training in algorithms, software and data engineering, operating systems, networking and AI. The particular priority depends on the available study plan, but my application goal is to make robot software reliable and reusable across hardware platforms.

## 建议反问

- Which courses or project options let MSc CS students work on distributed systems or intelligent robot software?
- How are practical projects evaluated: by implementation, experimental evidence, a written report, or a combination?
- Are there opportunities to collaborate with robotics laboratories or industry partners through the CS programme?

## 不要混淆

- 此处申请的是 CS，不是 MAIR；回答课程时引用 CS 页面。
- Kaihong CV 描述的是平台工作；不要将中间件、机器人操作系统或应用层接口说成同一个东西。
- “统一接口”不等于所有硬件的动力学、单位和安全限制相同。

---

回到[学校定制索引](README.md)。

## 2027 招生考核信息补充

CUHK-Shenzhen SDS 2027 招生页列出 MSc Computer Science。官方说通过材料初审后会另行提供考试相关信息，但没有公开统一题目、形式或时长；以个人邮件为准。[2027招生页](https://sds.cuhk.edu.cn/en/article/2462)。

按 CS 能力练：数据结构/算法、软件接口、并发时序、状态一致性、测试设计。P6 可答 “Why do timestamps and validity matter in a distributed robot platform?”；P5/P4 是 CS 方法的应用例。不要把机器人名词表当成计算机基础。

见[核验总表](../06_网络面试信息核验与练习优先级.md)。

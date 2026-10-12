# 02｜香港中文大学（深圳）：AI 与机器人方向

## 先把项目名称核准，这是这份申请的首要任务

提交包中的 Personal Statement 写的是 **M.Sc. in Artificial Intelligence and Robotics (MAIR), Robotics concentration**。当前官方页面存在批次表述不一致：SDS 的 2027 招生公告仍列 MAIR；MAIR 详情页却标注适用于 2026 及以前届，并让 Fall 2027 申请者查看新的 **MSc in Artificial Intelligence** 页面。新 MSc AI 页面另有 **Embodied AI and Robotics** concentration。不能把这些页面理解成学校已自动更改你的申请；必须按个人网申和面试邀请里的正式名称作答。

- [MAIR 官方页面](https://sds.cuhk.edu.cn/en/mair)
- [2027 MSc AI 官方页面](https://gs.cuhk.edu.cn/en/node/403)
- [SDS 2027 项目招生说明](https://sds.cuhk.edu.cn/en/article/2462)

面试前从网申页面/邀请信逐字确认：学位全名、方向、申请号、培养方案。如果你系统中是 MAIR，就使用答法 A；如果显示 MSc AI 的 Embodied AI and Robotics，就使用答法 B。不要说“学校已经把 MAIR 自动改成 AI”。

## 答法 A：仅当系统明确写 MAIR / Robotics concentration

> I applied to the M.Sc. in Artificial Intelligence and Robotics, with the Robotics concentration. My interest comes from practical work in manipulation, navigation and balance control. At Future Power, I worked on constrained inverse kinematics for dual-arm teleoperation; in other projects, I worked on mobile-robot planning and wheel-legged control. The programme’s robotics courses, including Robot Manipulation and Math Fundamentals for Robotics, match areas where I have practical exposure but still need stronger theoretical foundations. I also want to connect these topics with machine learning, optimization and embodied intelligence through the programme’s electives and project work.

## 答法 B：仅当系统明确写 MSc in Artificial Intelligence / Embodied AI and Robotics

> I applied to the MSc in Artificial Intelligence and selected the Embodied AI and Robotics concentration. My background is in computer science and physical robots, so I am interested in AI that connects perception and decision-making with real action. My projects include robot balance, mobile navigation, dual-arm teleoperation and edge-vision deployment. They have shown me both the value and the limits of fixed pipelines. I want to strengthen my foundations in machine learning, optimization and embodied robotics, and learn to evaluate a learned component under real timing, uncertainty and safety constraints.

## 为什么这个方向适合你

|材料中的经历|对应的学习问题|
|---|---|
|P2 VR 双臂遥操作与约束 IK|机器人操作、坐标/姿态映射、雅可比和奇异姿态|
|P5 EKF/AMCL + Hybrid-A* + TEB + MPC|概率状态估计、运动规划、优化和闭环跟踪|
|P7 LQR/VMC 轮腿控制|动力学、运动学、优化和实体交互|
|P4 YOLOv5/RKNN + 设备灌溉|学习模型如何进入具身任务并受安全规则约束|

## 可能追问与英文答法

### Why choose the robotics concentration rather than AI alone?

> My primary application area is robotics. I want the AI foundation, but I also need to understand manipulation, robot geometry and physical interaction. A robotics-focused path would let me connect learning methods with the systems I have already worked on. If my application is under the new MSc AI structure, I would express this as choosing the Embodied AI and Robotics concentration.

这句最后要按实际申请项目保留一个版本，不要在正式面试里同时说“两个我都申请了”，除非系统确实记录了两个志愿。

### What did the ballbot teach you about AI and robotics?

> It taught me that an algorithm cannot be evaluated only by its mathematical output. The balance controller depended on IMU and wheel feedback, timing, wheel limits and the arm-induced centre-of-mass shift. A model can guide the design, but hardware feedback and safe execution determine whether the result is usable.

### What is the difference between classical robotics and embodied AI?

> Classical robotics often uses explicit models and designed algorithms for estimation, planning and control. Embodied AI studies intelligent behaviour through interaction between an agent, its body and its environment, and may use learning as part of that loop. In practice, I would not treat them as opposites. I would choose a learned component only when it addresses a defined limitation and can be evaluated safely.

### What mathematical topic do you want to strengthen?

> I want to strengthen optimization and probability. In inverse kinematics, optimization helps balance task error and joint motion; in state estimation, probability provides a principled way to represent uncertainty. I have used these ideas in projects, and now I want to understand their assumptions and numerical behaviour more deeply.

### What research or capstone question interests you?

> I am interested in how a robot can maintain reliable task execution when perception or state estimates are uncertain. One possible study would compare a fixed model-based pipeline with a learning-assisted component under the same timing, sensor and actuator constraints. I would first narrow the question with a supervisor and define measurable criteria such as task error, failure cases and computational cost.

## 建议反问

- For my cohort, which official programme structure applies: MAIR with a Robotics concentration, or the MSc in AI with an Embodied AI and Robotics concentration?
- How are capstone projects assigned, and can students work on physical robot platforms?
- What mathematical preparation would you recommend for students entering the robotics or embodied-AI direction?

## 事实边界

- 你的 PS 里写了学习计划和课程名称；它们是申请材料里的意向，不等于已经选课。
- Mink/MuJoCo 求解约束 IK 不代表 MuJoCo 本身是实机驱动器；需要说明仿真/运动学计算和 ROS2-CAN 实机执行的分工。
- 不把“减少奇异位形附近速度放大”扩大成一个没有对照日志支持的百分比。

---

回到[学校定制索引](README.md)。

## 2027 Fall 项目名称与面试准备：重要更新

CUHK-Shenzhen 的官方页面目前不同步：SDS 的 2027 招生公告仍把 MSc in Artificial Intelligence and Robotics（MAIR）列入开放项目；MAIR 详情页则标注 “For 2026 and previous cohorts”，并把 Fall 2027 申请者导向新的 MSc in Artificial Intelligence 页面。新 MSc AI 页面另有 Embodied AI and Robotics concentration，且 FAQ 说奖学金会考虑 interview performance，但没有公布统一面试形式/题目。**不要自行推断 MAIR 已迁移或被替换。**面试时只能使用个人网申/录取邀请中的正式项目名与方向；若它与公开网页不一致，按申请记录回答并向项目方核实。[MAIR](https://sds.cuhk.edu.cn/en/mair) · [MSc AI 2027](https://gs.cuhk.edu.cn/en/node/403)。

练习：Why embodied AI and robotics? How does computer science help you integrate perception, planning and control? Which project proves you can connect algorithms with a physical system? 用 P2/P5/P7 支撑，并区分个人与团队贡献。

见[核验总表](../06_网络面试信息核验与练习优先级.md)。

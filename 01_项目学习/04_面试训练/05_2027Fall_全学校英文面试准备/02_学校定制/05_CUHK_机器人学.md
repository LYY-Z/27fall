# 05｜香港中文大学：MSc in Robotics

## 当前官方信息

CUHK MAE 官方 MSc Robotics 页面介绍机器人基础、移动机器人、感知、定位、地图、路径规划、控制、多机器人和机器人通信，并强调实践/研究训练。页面显示的培养信息属于 2026–2027 intake，申请截止信息为 2026 年 4 月 30 日；本次没有核实到后续批次页面。[官方项目页](https://www4.mae.cuhk.edu.hk/msc-in-robotics/)

面试前必须确认自己的申请批次、系统专业名称以及面试邀请是否对应这个项目。以下回答用于该专业匹配，不代表已证明当前轮次仍开放。

## 45–60 秒：Why CUHK Robotics?

> I am applying to the MSc in Robotics because my experience has developed across several separate robotic systems: balance control, legged locomotion, mobile navigation and dual-arm manipulation. I have implemented parts of these systems, but I want to understand the common foundations more rigorously. The programme’s coverage of robot systems, sensing, localization, planning and control matches the questions I encountered in my projects. I am also interested in experimental work, because my strongest learning has come from comparing a model or algorithm with what a physical platform can actually execute. My goal is to work on robotics algorithms in the Greater Bay Area.

## 为什么选 CUHK 的机器人学而不是笼统的 AI？

> AI is important to my future work, but my central engineering questions are about how a robot estimates its state, plans motion and interacts with the physical world. A robotics programme gives me a more direct way to study those linked problems. I would still use learning methods where they address a clear need, but I do not want to treat a robot as only a software model.

## 可能追问与英文答法

### Which project best represents your preparation?

> My mobile-robot navigation project is a good example of system integration. It connected EKF/AMCL localization, Hybrid-A* global planning, TEB local trajectory optimization and MPC tracking on a car-like platform. Each module had a different input and output, so the state frame, timing and vehicle constraints mattered. I can explain the algorithm chain, while I would avoid reporting performance figures that are not supported by matched logs.

### What is the difference between a path and a trajectory?

> A path describes a geometric route through space. A trajectory also assigns time or velocity to that route. A controller needs a time-related reference or motion command, not only a line on a map. In my navigation project, the planner and controller therefore had to exchange compatible pose, heading and motion information.

### How do you validate a robotics algorithm?

> I would start with unit or model checks, then use repeatable simulation or recorded data, and finally run a controlled hardware test. I would define metrics before the experiment, such as tracking error, completion rate, computation time and limit events. I would record sensor freshness and coordinate frames so that a failure can be traced to the algorithm or to the surrounding system.

### What do you hope to research?

> I am interested in reliable mobile-robot navigation under imperfect state estimates. A possible starting question is how localization uncertainty affects local trajectory tracking near obstacles. I would refine the scope with a supervisor, define comparable test cases and report both tracking performance and failure conditions.

### What is a limitation in your current experience?

> Most of my work has been engineering and implementation on specific platforms. I have not yet completed a substantial independent research study with a carefully controlled comparison. I want to improve my experimental design, literature review and statistical interpretation so that I can distinguish a real algorithmic improvement from a change in conditions.

## 建议反问

- For the intake I applied to, which robotics courses and experimental projects are expected to be available?
- How are project topics matched with supervisors, and what kinds of hardware platforms can students use?
- Does the programme encourage students to integrate sensing, planning and control in one project?

## 事实边界

- 不把 CUHK 的 programme 页与 CUHK-Shenzhen 的 MAIR/CS 页面混用。
- 说“我搭建/实现了链路”时准备解释哪些模块由你做、哪些由团队提供。
- 官网介绍某项课程或机会，不意味着你已被分到该课程/导师。

---

回到[学校定制索引](README.md)。

## 面试与2027批次核验补充

官网介绍机器人基础、控制、感知、实践项目和独立研究；当前招生页可见批次仍需和个人网申记录核对，未查到2027授课硕士固定面试题目/形式。不要把 CUHK 本科 Robotics 面试信息挪作 MSc 证据。[MSc Robotics 项目页](https://www4.mae.cuhk.edu.hk/msc-in-robotics/) · [Graduate School 项目页](https://www.gs.cuhk.edu.hk/programmes/engineering/msc-robotics)。

练习：How do you derive a Jacobian? How do sensors affect state estimation? What is the difference between a planned trajectory and a motor command? How would you validate a controller safely? 这些是根据课程和经历设计的练习题，不是官方题单。

见[核验总表](../06_网络面试信息核验与练习优先级.md)。

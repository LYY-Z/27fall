# LangGraph规则工具与决策

## 学习目标与入口

本章解决：Agent的状态和节点如何工作，为什么建议还要经过执行策略。

相关项目：P4。先修：[基础课程总览](../../../01_通用基础/00_基础课程总览.md)。建议先读本项目全貌，再按章节编号阅读。代码入口：[教学实验与完整命令](../../../03_代码实验/02_项目实验/P4/README.md)；代码未运行核对，输出预期不能当实测。

## 0. 先用白话定位本页

LangGraph可以先当作一张可运行的流程图：节点检查输入、写回结果，连线决定下一步。它负责组织规则和建议流程，但不自动证明物理设备已执行。读本章从一条简单湿度事件开始，跟着状态经过规则、建议、执行检查，再区分建议文本、命令请求和设备回报。

读的时候依次做三件事：说出实际物体和目标，标明每个输入/输出的含义与单位，再沿代码确认这一步真实被谁调用。教学示例帮助你理解因果关系，只有源码、日志或实验记录支持的内容才能说成项目事实。

## 1. 图不是另一个神经网络

LangGraph组织状态与控制流程：node读取state返回更新，edge决定下一个node。源码_build_graph建sensing/supervisor/care/alert/execution/skip，sensing纯规则判fast_path；硬规则直接execution，其他supervisor再分care/alert/skip。

状态含sensor_snapshot、detections、软阈值、历史/RAG、建议与hardware_commands。LLM解释和规则控制不同：规则低延迟可预测，LLM能组合信息但会受上下文、输出格式和错误推理影响。

## 2. fast path与fallback

源sensing调用check_fast_path，命中跳过LLM；LangGraph缺失/异常有fallback_rule。不能只说“多Agent自动决策”，必须说明输入、条件、哪个分支真正调用LLM、哪个只做确定规则。

## 3. 执行边界

execution将commands白名单验证、构造硬件命令和Web广播；source event_id/scope去重减少重复处理。建议不等于执行成功，execution_summary文本也不自动是设备实测回执。

教学decision_step返回action/reason/requires_policy_check=True，不调用LLM、不发送命令。调用方再检查模式、新鲜度和规则才模拟执行。模型说start不能越过人工off；功能边界是软件设计，不靠提示词一句话保证。

Graph API当前版本见[官方文档](https://docs.langchain.com/oss/python/langgraph/graph-api)，项目当时依赖版本需记录，不能最新版行为替代源环境。

## 4. 把State、Node和Edge想成一张不断传递的工作单

假设服务收到一条“土壤读数偏低”的事件：

1. **State**是一张工作单，里面放湿度快照、检测快照、分析类型、规则结果、知识上下文、建议和待发命令。
2. **Node**是处理工作单的一步，例如读取阈值、筛选检测、生成护理建议。
3. **Edge**是下一步路线，例如快速规则命中后去execution，未命中去supervisor。
4. 每个节点返回一部分新字段，后续节点再读取；同一个state会在图中逐步丰富。

所以LangGraph本身不是识别植物的神经网络，也不是自动学会控制的策略。图的结构和条件由程序员写；其中某个节点可能调用LLM，其余节点可以只是普通Python规则或数据整理。

## 5. 当前源码中的六个节点怎样分工

| 节点 | 用白话说它做什么 | 主要分支 |
|---|---|---|
| sensing | 先用确定规则检查当前事件 | 普通传感事件可检查fast path；detect范围不复用传感快路径 |
| supervisor | 判断是否需要后续分析、走care/alert/skip | 两类触发都没有时直接skip；需要路由时调用LLM |
| care | 生成养护建议 | 使用传感器状态和检索到的养护知识 |
| alert | 分析视觉/风险事件 | 组合检测、传感和知识，可能形成待校验命令 |
| execution | 检查命令并输出桥接结果 | 校验允许的设备和动作，再交给结果消费者 |
| skip | 记录无需干预的结果 | 不发硬件动作 |

可以用路线表示：

~~~text
sensing
  ├─ 规则快速路径命中 ─────────> execution
  └─ 未命中 ─> supervisor
                 ├─ care
                 ├─ alert ──需要后续执行时──> execution
                 └─ skip
~~~

**fast path和skip方向相反**：fast path是“条件明确，走短路线处理”；skip是“无需处理，结束本次事件”。它们都不是LLM。

## 6. 规则、LLM与执行策略各自负责哪一段

- **硬规则**适合清楚、必须可预测的保护条件，例如湿度极低时的预设动作。
- **软阈值**适合触发“需要进一步关注”，它可以把事件送去分析，但不等于最终设备动作。
- **LLM**适合组织自然语言、综合知识、提出建议；它的文本可能不完整、错误或违反策略。
- **执行检查**负责把建议限制为系统允许的设备和动作，并检查模式、范围、新鲜度及人工停止状态。
- **设备执行与反馈**发生在服务之外，需要单独的通信和设备状态证据。

白名单只回答“命令名称是否在允许集合里”，不能独自回答“当前设备是否在线、这条数据是否新、用户是否允许、参数是否安全、设备有没有真的动作”。提示词不是安全边界。

## 7. 项目中的记忆与RAG不是凭字段名猜出来的

可以把记忆分成四类：

| 类型 | 例子 | 当前源码对应路径 |
|---|---|---|
| 工作状态 | 这次传感和检测的快照、当前路由 | LangGraph传递的state |
| 情景记忆 | 最近湿度、温度、光照和历史动作 | MemoryStore记录，MemoryAgent检索摘要 |
| 语义知识 | 病害处理、养护说明 | 知识表检索；有embedding时走向量相似度 |
| 程序记忆 | 可调软阈值 | care rules存储与加载 |

代码中的MemoryStore优先尝试PostgreSQL；连接失败或未配置时可降级。语义检索有向量检索路径，也有关键词匹配/内存知识降级。MemoryAgent可取最近10条传感历史和最多5条动作历史，再把摘要放进Agent上下文。知识检索条数、数据库是否连接、embedding是否可用，需看启动状态和运行日志，不能只凭源码推断本次运行用了哪种路径。

这就是RAG的实用含义：先从外部知识中找少量相关材料，再把材料作为上下文交给生成节点。检索命中不代表材料一定正确，LLM引用材料也不代表建议经过了设备安全校验。RAG改善信息来源，不提供动作权限。

## 8. “记过动作”不等于“动作已被物理验证”

当前服务在图完成后，若final state里有hardware_commands，会把一条action log写成outcome=executed；之后AgentBridge才把结果交给server命令消费者，命令再进入TCP发送队列。因此日志字段executed表达的是当前软件路径的分类，不能单独证明设备收到了命令或水泵已运行。

MemoryAgent以后如果读取这类记录并说“最近执行过”，要把它理解成软件记录，不要自动升级为流量传感器或电机回执。理想记录应把decision_id、command_id、queued、sent、device_ack、reported_state、physical_feedback分别保存。

## 9. 去重能挡住什么，不能挡住什么

当前Agent在内存里按event_id和scope组合去重，清理窗口约60秒；sensor、detect等scope可以分别处理。这能减少重复分析，但它不是持久去重，也不是设备端幂等。

源码在调用图之前就标记事件已处理。如果之后LLM、数据库或命令桥接失败，重发的同一事件可能在窗口内被跳过；服务器重启后内存去重表消失；同一个动作若换了event_id，也可能重复执行。真正安全的重试还需要独立action_id、设备端重复命令识别、超时和回执策略。

## 先把本章几个词换成普通话

- **State状态**：当前事件、传感器、建议和执行结果的资料表。
- **Node节点**：读取部分状态、做一个步骤并写回结果的小函数。
- **Edge边**：决定完成这一步后进入哪个节点；它是流程路线，不是神经网络权重。

## 再走一遍：从实际输入到下一模块

把state想成一张不断补充的表，LangGraph节点是读表、判断、写结果的小步骤，边决定下一步去哪。新湿度事件先过规则检查；符合确定条件可走fast path，其他情况才可能经过建议节点。最后执行仍要检查人工模式、数据新鲜度和允许命令。例如模型建议start，但当前manual_request=off，执行策略仍应保持关闭。这样模型的建议和设备允许做什么被分开，网络模型失败时也可保留规则路径。event_id去重能减少同一事件重复处理，但服务器去重不证明设备侧绝不重复动作；仍需设备回执和幂等逻辑。

## 一次完整手算

state.moisture=40、auto、新鲜，建议action=start。执行策略start56/stop65允许on；若mode=manual、manual_request=off，同一建议仍应off。传感规则10ms、LLM假设1s，fast path可避免这次1s调用，但这些是教学耗时，非源实测。

## 失败条件与排查

LLM输出非法结构；快慢路径相互覆盖；旧传感与新检测拼接；重复事件重复开泵；把广播摘要当硬件ACK。

## 中英文解释与追问

中文回答主线：先指出输入和输出，再说明模型、假设、实际源码调用和异常。本人工作、团队代码和新教学示例分开陈述。

英文参考：The graph routes events through deterministic rules and optional reasoning nodes. The execution layer validates permitted actions; a generated suggestion is not an actuator acknowledgement.

追问：What would you measure before claiming that this works on hardware?

参考：I would log time-aligned inputs, outputs, tracking errors and limit events, and compare the measured results with a defined baseline. Reading code alone does not establish hardware performance.

## 四类练习与答案

1. 概念：StateGraph等于训练模型？答：不是流程编排。
2. 计算：manual off能被建议覆盖吗？答：教学策略不能。
3. 代码：fast_path走哪？答：execution。
4. 结果：LLM失败还能基本灌溉？答：核对fallback和本地控制。

## 复习与下一步

遮住公式，用一张纸写出本章数据链、每个量的单位、一个手算和两种失败。继续阅读本项目下一编号章节；最后一章转源码阅读与运行。能解释后再进入英文问答，不把文档交付记作已经掌握。

## 精读补充：把中间步骤讲清楚

### 本章在完整周期中的位置

sensing先规则fast path，再可选推理节点；六节点不是六个模型。event_id:scope去重防重复分析，但先标记后执行可能留下失败记录，不能据此宣称硬件exactly-once。

先回到[完整源码周期](../02_源码阅读与运行/02_一个周期的调用与数据流.md)，定位本章之前输入由谁产生、之后结果被谁消费；再读[对应基础推导](../../../01_通用基础/06_导航_视觉与机器学习/08_Agent状态工具与执行边界.md)。不要只背中间一个函数或矩阵。

### 用纸笔完成这一页的验收

1. 从本章数值例重算每个中间量，写单位和输入形状。
2. 对照[源文件地图](../02_源码阅读与运行/01_源码版本与文件地图.md)，指出活动分支和被注释的区别。
3. 解释上述特有误读点，并给一条能区分原因的日志字段。
4. 先用中文说清输入→计算→输出，再用本章英文口述；涉及个人贡献时查材料证据，不把教学重建说成历史部署。

## 历次疑惑归纳：Agent 能建议什么，系统允许执行什么

按问题主题的完整复习入口：[P4 历次问题归纳与完整学习地图](../05_中英文面试/05_历次问题归纳与完整讲解.md)。

- **State、Node、Edge 是流程编排的数据、步骤和分支。**LangGraph 管理状态如何在节点之间传递，不是又训练了一个神经网络。
- **Fast path 是明确规则的短路处理，fallback 才进入更丰富的上下文/LLM建议。**两条路径都要检查输入新鲜度和已有人工模式，不能让 LLM 越过硬件安全策略。
- **建议必须经过独立执行门。**白名单、设备能力、命令时长、当前模式和去重状态是执行层要检查的条件；`execution_summary` 是软件说明，不是设备 ACK。
- **记忆分当前状态、历史记录和知识资料。**RAG 检索片段供模型参考，不是在线训练，也不保证内容正确或最新；数据库/embedding 未就绪时可能降级，源码存在检索类不证明当前启动实际使用向量库。涉及设备动作仍须检查来源时间、人工模式、白名单和设备回执。
- **去重不是 exactly-once。**还要考虑命令 ID、设备侧重复处理、超时重试、物理反馈与状态对账。

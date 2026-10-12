# 02 结构体类RAII与接口

先修：[01_C与C++内存指针引用](01_C与C++内存指针引用.md)。项目：P4、P6。实验：[数据结构与状态同步](../../03_代码实验/01_基础实验/03_数据结构与状态同步/README.md)。

## 1. 从一堆变量到一个明确对象

同一个电机的序号、速度、在线状态放在一个Feedback结构体，可以让“这几个值属于同一次反馈”更清楚。类除了保存数据，还定义可执行的操作与内部规则。抽象接口让上层用相同的`execute`调用不同设备，而不需要知道UART或网络细节。

```cpp
struct Feedback { unsigned long sequence; double speed; bool online; };
class DeviceAdapter {
public:
    virtual ~DeviceAdapter() = default;
    virtual Feedback readFeedback() = 0;
    virtual bool execute(double target) = 0;
    virtual void stop() = 0;
};
```

这里的纯虚函数表示派生类必须实现该动作。通过基类指针销毁派生对象需要虚析构。接口统一方法名，不自动统一单位、时效、错误处理；这些还要写合同。

## 2. RAII为何能管理资源

RAII把资源寿命绑到对象寿命：构造获得资源，析构释放资源。锁守卫离开作用域会解锁，即使提前return或抛异常也能释放。`std::unique_ptr`表示唯一所有权，`shared_ptr`表示共享所有权；后者不等于所指对象内部的数据已线程安全。

```cpp
{
    std::lock_guard<std::mutex> guard(mutex);
    latest = feedback;
} // 自动解锁
```

这比在每个return前手工unlock更容易保持正确。不能让对象析构时还有线程访问它；应先发停止信号，再join线程，最后销毁共享资源。

## 3. 手算一个生命周期

步骤1建立模拟设备；步骤2执行目标0.5m/s；步骤3收到sequence=8、speed=0.4；步骤4停止，目标置0；步骤5销毁。

若设备离线仍返回旧0.4，上层可能认为速度跟踪正常。因此Feedback需online和timestamp或sequence。若execute返回true只表示排队成功，应在接口说明它不表示“电机已达到0.5”。执行回执与物理到达是两个阶段。

## 4. 继承与组合怎么选

设备“是一种适配器”可用继承；控制器“拥有一个通信通道”可用组合。可替换组件、清晰所有权比层层继承更重要。P6需要从实际factory/adapter调用确认能力接口，而不能由目录名认定实现了全平台抽象。

## 5. 排错与边界

失败一：基类无虚析构，通过基类销毁派生对象会产生未定义行为。失败二：析构未停止后台线程，访问已释放内存。锁住太久会阻塞反馈；不要持锁等待网络回复。

实验：[C++队列](../../03_代码实验/01_基础实验/03_数据结构与状态同步/README.md)，后续[P6课程](../../02_项目课程/P6_深开鸿KaihongMeta/README.md)有适配器模拟。

## 6. 英文与练习答案

“I separate a device interface from its transport implementation. RAII gives resources a clear lifetime, while feedback must carry enough information to distinguish fresh state from stale state.”

追问：Does a common interface guarantee identical behavior? No; units, deadlines, acknowledgements and failure behavior need explicit contracts.

1. 概念：execute成功与到达目标相同吗？答：可能只表示命令已接收，需另读反馈。
2. 计算：目标0.5、反馈0.4，误差？答：0.1m/s；反馈过期时不能作为当前误差。
3. 代码：何时join线程？答：先发终止信号，唤醒阻塞等待，再join，最后释放资源。
4. 解释：抽象接口增加可替换性，却不应隐藏哪些事？答：单位、时效、权限、执行失败、真实硬件能力。

下一章：[03_容器复杂度与数据结构](03_容器复杂度与数据结构.md)。复习时先不用术语解释例子，再复述英文。

## 精读补充：把中间步骤讲清楚

### A. 统一接口到底统一了什么？

上层调用`set_speed(0.5)`，电机A底层需要rad/s、电机B需要rpm。适配器可在内部完成换算，让公开合同统一成轮轴m/s；也可以公开不同单位，但必须显式标注。只把函数名都叫execute，却把0.5解释成不同动作，不能算语义上可替换。

接口合同还要说明：成功是已排队、已写入驱动、收到设备ACK还是达到目标？“bool=true”不足以同时表达这四个阶段。可使用带action_id和状态的结果，由独立反馈判断物理完成。

### B. RAII是按寿命释放，不是定时取消任务

mutex守卫离开作用域解锁；socket对象销毁关闭资源。若后台线程仍在阻塞读取，销毁资源前需定义停止/唤醒/join顺序。不能仅因使用shared_ptr，就认为程序会准时停止；共享所有权可能让资源活得更久。

### C. 用一张对象关系表读P6

设备管理器拥有注册设备；处理器临时借用或持有设备；线程池拥有排队任务；任务参数按值或引用捕获。对每条关系标“谁负责销毁、谁可能最后使用”。这比背“用了工厂模式/继承”更能解释项目安全退出与异常恢复。

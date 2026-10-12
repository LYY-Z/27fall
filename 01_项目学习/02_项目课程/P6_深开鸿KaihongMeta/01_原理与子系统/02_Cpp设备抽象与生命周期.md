# 02 C++设备抽象：从一个对象到一次设备调用

本章沿“创建对象 → 初始化 → 找命令 → 执行 → 释放”解释C++。共同流程见[平台定位](01_平台版本组件与申请范围.md)，实际文件见[源码地图](../02_源码阅读与运行/01_源码版本与文件地图.md)。

## 1. 类、对象和设备是怎样对应的

`GroundLockHandler`是处理地锁的**类**，定义了有哪些数据和函数。程序创建出的某个实例是**对象**。它保存设备ID对应的端口和状态，并提供Up/Down等行为。

一个处理器对象可能管理多台设备：`devicePropertyMap_`用deviceId查各自信息。因此不能先假设“一个对象一定对应一台地锁”。要看成员表和生命周期参数。

代码中的`this`指当前对象；`this->devicePropertyMap_`就是这个对象拥有的设备表。回调捕获`this`，意味着回调之后仍会访问该对象，所以对象必须活到回调结束。

## 2. 继承在这里共享什么

本地定义为：`BaseDeviceHandler : public IDeviceHandler`。地锁处理器再继承基类。可以把层次读成：

```text
IDeviceHandler：规定对外有哪些操作
    ↓
BaseDeviceHandler：实现共同流程
    ↓
GroundLockHandler：提供地锁特定初始化和操作
```

对外接口规定函数签名，包括deviceId、cmd、input、output。基类实现共同查找和调度，子类负责端口、命令注册、协议和数据解析。

**重要源码细节：**`ExecCommand`在基类中是`override final`，地锁子类不再覆盖这个公共入口。真正的up行为来自`OnInit`中注册到命令表的处理函数。不要把所有命令分派都说成“直接调用子类重写的ExecCommand”。

## 3. virtual、override和final各管哪件事

- `virtual`使通过基类接口调用时，可以选择对象真实类型对应的实现。例如基类初始化调用`OnInit`，实际对象是地锁，就进入地锁版本。
- `override`要求编译器检查这个函数确实覆盖了基类虚函数。参数写错时能发现，而不是悄悄产生另一个函数。
- `final`禁止下一层再覆盖，以便保持共同入口流程。
- 虚析构使通过基类指针销毁派生对象时，执行完整析构链。若以非虚基类析构删除派生对象，C++语义可能是未定义行为，不仅仅是“少清理一点”。

下面是**独立教学例子**，不冒充平台原文件：

```cpp
struct Device {
    virtual ~Device() = default;
    virtual void stop() = 0;
};
struct MockDevice : Device {
    void stop() override { value = 0; }
    double value = 0;
};
std::unique_ptr<Device> d = std::make_unique<MockDevice>();
d->stop(); // d类型是基类指针，对象真实类型是MockDevice
```

`=0`声明纯虚函数，要求可实例化的派生类提供实现。`d->stop()`是通过指针调用，不代表硬件命令已经送到电机；本例只修改内存。

## 4. 注册回调怎样把up接到Up函数

源码使用类似以下绑定：

```cpp
RegisterCommand(deviceId, CMD_ID_UP,
    std::bind(&GroundLockHandler::Up, this,
              std::placeholders::_1,
              std::placeholders::_2,
              std::placeholders::_3));
```

逐项读：`&GroundLockHandler::Up`选择成员函数；`this`固定在哪个对象调用；三个占位符等待后来提供deviceId、input和output。注册表保存的是一个以后可调用的函数对象。

随后`ExecCommand`找到它，worker执行`handler(deviceId,input,output)`。`cmd`用于**选择**handler，不会作为这三个参数之一传给Up。Up函数再从deviceId找到该设备端口，调用地锁写寄存器路径。

`std::function`是装载这种可调用对象的共同类型；它本身不是新线程。什么时候、在哪个线程调用，取决于下一章的线程池。

## 5. Init具体做了什么

按本地调用流程：创建/取得线程池；初始化属性上报；调用子类OnInit；OnInit注册up/down并查询通道信息；保存端口和初始缓存；设置ListeningTask轮询回调；基类成功后登记设备并设置online与schedule。

**构造对象与Init成功不同。**构造只建立C++成员；Init才建立运行所需的关系。`OnInit`成功也不等于刚刚收到地锁实测，当前初始化路径可以仅完成配置和登记。

如果初始化中途失败，应该核查已经注册的回调、建立的连接和登记记录由谁撤销；不能因为析构函数存在，就假定所有部分初始化状态一定正确清理。

## 6. unique_ptr、shared_ptr和RAII为什么会出现

`unique_ptr`表达独占所有权：一个所有者负责释放对象，通常不能复制所有权，可通过move转移。`shared_ptr`允许多个所有者共享寿命，最后一个所有者释放时销毁对象。它们都不会自动保证对象内部数据的并发访问安全。

RAII把资源释放放在对象的析构过程，例如`lock_guard`离开作用域自动解锁。它解决资源何时释放；互斥锁、队列或快照才解决不同线程如何协作。

源码把一些类型仅在头文件前向声明，而在cpp实现构造/析构。前向声明只告诉编译器“有这个类型”；销毁`unique_ptr`持有的对象时需要完整类型，因此销毁点放在包含完整定义的cpp中。

## 7. Release与正在运行的任务为什么必须一起读

理想的关闭合同是：拒绝新任务 → 明确处理排队任务 → 等待或取消在途任务 → 停止轮询 → 释放连接和状态 → 销毁对象。这个顺序是**设计目标**，当前Release是否满足要沿源代码核查。

危险例子：回调已入队并捕获`this`；对象先销毁；worker后来执行回调。此时指针地址还在，地址对应的对象却不再有效。把指针复制一份并不能延长对象寿命。

另外，`join()`仅等待线程退出，不证明排队任务全部执行完。当前线程池关闭后可能留下没有完成结果通知的任务，详见[线程池](03_线程池回调共享状态与调度.md)。

## 8. 复习验收与英文口述

依次解释：对象是谁；基类提供哪部分流程；OnInit如何调用；cmd如何选到回调；output由谁写；对象关闭时谁还可能访问它。不要只背四个C++关键词。

英文：*The base class owns the common command flow. Device-specific callbacks are registered during initialization. Virtual dispatch, resource ownership and thread synchronization solve different problems.*

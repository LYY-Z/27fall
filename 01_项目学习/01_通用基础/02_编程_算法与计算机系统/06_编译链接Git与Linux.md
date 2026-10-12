# 06 编译链接Git与Linux

先修：[05_PythonNumPy与数组形状](05_PythonNumPy与数组形状.md)。项目：P2、P3、P4、P6、P7。实验：[数据结构与状态同步](../../03_代码实验/01_基础实验/03_数据结构与状态同步/README.md)。

## 1. 从源码到程序发生了什么

C/C++源码先预处理（包含头文件、展开宏），编译成目标文件，再链接把符号引用接到具体实现，得到可执行程序。头文件通常声明函数；.cpp/.c提供实现。只有声明没有被链接进来的实现会产生undefined reference。

例：main.cpp调用`double convert(double)`，math.cpp定义它。编译main.cpp能通过因为知道函数签名；最终链接遗漏math.cpp就找不到函数代码。相同函数在多个目标里重复定义也会失败。

## 2. 完整命令和路径

从申请材料目录编译教学队列：

```powershell
g++ -std=c++17 -pthread '.\01_项目学习\03_代码实验\01_基础实验\03_数据结构与状态同步\state_demo.cpp' -o '.\state_demo.exe'
.\state_demo.exe
```

Bash：`g++ -std=c++17 -pthread '01_项目学习/03_代码实验/01_基础实验/03_数据结构与状态同步/state_demo.cpp' -o state_demo && ./state_demo`。这是给学习者的命令，本轮未编译。编译器的线程实现必须可用，存在g++路径不代表pthread一定配置好了。

含空格中文的路径必须完整引用。Linux路径区分大小写，Windows通常不区分；把`Config.h`写成`config.h`可能在Linux失败。相对路径以当前工作目录为准，不以源文件位置为准。

## 3. 手算一次构建依赖

main.o需要convert；math.o提供convert；库libmotor提供send。链接顺序、库目录、ABI与目标架构要匹配。x86电脑编译的可执行不能直接放到STM32；STM32需要交叉编译器、链接脚本、启动文件和芯片配置。

ROS构建还包含消息生成、包依赖和环境source。Python脚本能启动不代表ROS话题/模型文件已存在。P4 RKNN推理要求匹配硬件与runtime；转换工具和板端runtime职责不同。

## 4. Git如何记录版本

工作区是当前文件；暂存区是下一次提交选中的内容；commit是快照；branch是提交指针。`git status`看差异，`git diff`看未暂存，`git diff --cached`看暂存。不要把“有源码”误当“某提交部署过”。记录commit或文件SHA256、配置和日志更有意义。

教学材料保存与原始项目源码修改应区分。既有暂存内容可能属于别的任务，不使用全库add/commit来保存本次局部工作。

## 5. 排错、英文和练习

编译失败先看第一个错误；链接失败看缺符号及目标列表；运行找不到文件看cwd与路径；固件不能运行看架构/入口/硬件。不要只添加随机头文件。

“Compilation checks each source file, while linking resolves references across object files and libraries. For an embedded target, I also need the correct toolchain, linker script and board configuration.”

追问：Why does code compile but fail to link? A declared function may have no linked definition.

1. 概念：头文件等于实现吗？答：不一定，模板/inline等可能包含实现，一般声明还需相应定义。
2. 计算：3个源文件各1个目标，漏链接1个提供函数的目标？答：调用该函数会找不到定义。
3. 代码：中文空格路径怎样传参数？答：引用完整路径，不拼接未引用字符串。
4. 解释：代码提交能证明实机效果吗？答：不能，还需构建版本、参数、设备和运行记录。

下一章：[07_进程线程同步与操作系统](07_进程线程同步与操作系统.md)。复习时先不用术语解释例子，再复述英文。

## 精读补充：把中间步骤讲清楚

### A. 看懂一个链接错误需要哪三条线索？

调用处：main调用convert；声明处：头文件告诉编译器convert接收double并返回double；定义处：另一.cpp提供函数体。构建配置必须把定义所在目标文件一起链接。声明只回答“怎么调用”，不提供真正实现。

如果定义签名改成`convert(int)`，main需要的double版本仍可能不存在。C++名字修饰使不同签名对应不同符号，因此“文件里有同名函数”还不够。

### B. 配置与可执行也需要对应

P1有多个相似控制器源文件，CMake指向哪一个、launch请求哪个type，决定阅读对象。P5的launch可执行名与CMake生成名不一致时，理论正确也可能根本未启动预期节点。

Linux运行还受工作目录、环境变量与共享库路径影响。源码位于一个目录不代表所有相对文件都相对源码解析；教学Python使用`--out-dir`显式控制输出，减少这个歧义。

### C. 版本证据由几件事组成？

源文件/commit、依赖版本、配置、构建目标、部署设备、日志应对应同一次运行。文件SHA证明当前文件字节，不证明是谁写的或曾上机。面试中说“this source snapshot”与“the deployed version I used”要有不同证据支持。

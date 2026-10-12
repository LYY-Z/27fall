# 05 图像检测YOLO与NMS

先修：[04_车辆模型与路径跟踪](04_车辆模型与路径跟踪.md)。相关项目：P4。目标：把本章算法接到输入、输出、手算和工程失败。

## 1. 图像怎样变成结构化事件

摄像头输出像素，预处理调整颜色、尺度与布局，网络输出候选框/类别分数，后处理恢复原图框并过滤，形成timestamp、class_name、confidence、bbox事件。框不是电机动作；感知结果还要进入决策和策略检查。

检测回答对象在哪里/是什么；分类通常回答整张图是什么；分割给像素类别。YOLOv5具体输出/损失与export版本有关，读取项目模型和后处理，不套最新YOLO版本接口。

## 2. IoU完整手算

框A=[0,0,2,2]，B=[1,0,3,2]，xyxy像素坐标。面积各4，交叠宽1高2面积2，联合4+4-2=6，IoU=2/6=1/3。相同框IoU=1，不相交0。

NMS先取最高分框，删除与其IoU超过阈值的同类别候选，再处理剩余。A分.9、相同B分.8、阈.5，只保留A。不同类别通常分开NMS，不能无说明把所有类别混删。

## 3. confidence不是准确率

单个框分数.9表示模型在该输出规则下的分数，不等于现场90%必定正确，也不等于测试集准确率90%。需用标注数据评价precision、recall等，分数可能未校准。阈值提高通常减少候选，漏检与误检权衡要测。

letterbox缩放后有padding，坐标恢复需先去padding再除scale。原图640×480到640×640加上下80，网络y=100对应原图20，不是100。

## 4. 实验与失败

[NMS实验](../../03_代码实验/01_基础实验/12_搜索图像与协议/README.md)只演示框后处理，不运行YOLO网络。P4真实图像源是V4L2/RKNN链。失败：RGB/BGR颠倒；NCHW/NHWC不匹配；模型输入归一错误；旧timestamp；框坐标没还原。

## 5. 英文与练习

“Detection converts image data into objects, classes and boxes. NMS removes overlapping candidates, while confidence is a model score rather than a measured system accuracy.”

追问：How do you handle an old detection? Validate its timestamp and reject or downgrade stale evidence before deciding actions.

1. 概念：NMS训练网络吗？答：后处理筛选。
2. 计算：相同两框IoU？答：1。
3. 代码：bbox x2<x1？答：拒绝无效框。
4. 解释：分数高仍误灌溉？答：检查模型类别、数据/阈值、事件时效与执行规则，不把分数当真实状态。

下一章：[06_训练损失梯度与模型评估](06_训练损失梯度与模型评估.md)。

## 精读补充：把中间步骤讲清楚

### A. 检测框还原的完整步骤

原图1280×720缩放到640×360，再上下各补140成为640×640。网络框[100,160,300,340]，去padding得[100,20,300,200]，除缩放.5得到原图[200,40,600,400]。直接除.5但不去padding，y就会偏280像素。

两个同类重叠框分.9/.8，先取.9再按IoU删.8；不会平均成新框，也不会从NMS得到真实准确率。若模型版本含不同输出布局，必须先解析候选再NMS，不能套另一个版本的列索引。

# 07 里程计AMCL与多传感器接口

先修：[06_EKF线性化与观测](06_EKF线性化与观测.md)。项目：P2、P5。学习目标：说清数据来源与统计假设，完成本章手算，再读代码。

## 1. 局部连续与全局地图约束

轮里程计根据轮转动累积运动，短期连续，打滑/参数误差长期累积。IMU提供角变化；EKF可融合局部运动观测。AMCL用地图与激光观测对粒子位置假设加权并重采样，提供全局定位约束。它不是同一个Kalman更新公式。

一般TF组织map→odom→base→sensor：odom→base保持局部连续但漂移；map→odom补全局偏差；base→sensor是安装外参。具体发布节点需看启动配置，不能多个节点同时发布同一段冲突变换。

## 2. 手算一次里程计

差速轮半径.1m,L=.4m，左右角速度6、14rad/s，线速度.6、1.4，车体v=1,ω=2。dt=.1，yaw加.2rad。简单Euler在旧yaw=0处p_x加.1,p_y不变；准确恒速转弯轨迹半径v/ω=.5，增量[.5sin.2,.5(1-cos.2)]≈[.09933,.00997]。

采样小可以减小Euler差异，不能修复打滑。左右都转不代表车体一定按轮式公式移动。

## 3. 全局修正为何看起来跳变

假设odom估计车在10m，地图定位发现实际9.7m，map→odom平移改-.3。odom→base仍连续，map下的车位置被纠正。规划与局部控制应按各自需要使用正确系，不能把全局跳变直接当车物理瞬间移动.3m。

如果跳变远超合理范围，应看定位多解、激光质量、时间外参和创新门限，不把任何跳变当正常。不同滤波器输出相关时重复融合会过度自信，例如轮里程计已含IMU又把同一IMU作为独立测量，独立假设可能不成立。

## 4. 接口表必须逐字段做

每条观测记录timestamp、frame_id、字段顺序/单位、噪声协方差、有效位、频率、处理延迟。位置与速度测量H不同；来源相关/旧数据要明确。P5真实EKF参数可配置融合哪些分量，配置存在不等于该topic正在发布。

## 5. 实验、失败与英文练习

基础Kalman实验理解预测与测量职责，P5教学车辆实验理解路径；真实ROS回放依赖系统与数据。失败：两个定位节点争同段TF；把map跳变当速度；轮径与轮距错误；低质量数据仍高权重。

“Wheel odometry is locally continuous but can drift. Map-based localization adds global constraints. I separate those roles through the map, odom and base frames and check that each transform has one intended publisher.”

追问：Why not fuse every available estimate independently? Some estimates reuse the same measurements and their errors are correlated.

1. 概念：AMCL等于EKF吗？答：不，粒子定位与高斯局部估计结构不同。
2. 计算：odom=10，map偏移-.3？答：地图位置9.7m。
3. 代码：检查配置后还需什么？答：topic真实字段/时间/频率、TF发布和运行日志。
4. 解释：轮转了位置不变？答：可能打滑/轮离地，需接触与外部观测。

下一章：[08_时间对齐接触与异常数据](08_时间对齐接触与异常数据.md)。

## 精读补充：把中间步骤讲清楚

### A. map和odom为什么可以同时存在

轮速积分希望连续，短期适合控制，却会累积漂移；全局定位希望贴合地图，但新观测可能修正旧位置。设odom下车在10m，地图观测提示9.7m，可以令map→odom平移−.3m，odom→base仍10m；两者相加得到map下9.7m。不能把两个坐标数直接相减当传感器互相冲突。

控制器选择的参考系需一致：路径在map，状态在odom时先转换；不要把map修正跳变误认为车瞬间倒退.3m。AMCL是地图定位，轮里程计是运动积分，EKF是所选模型/观测的融合，不能只靠输出都叫pose就互换。

### B. 重复信息为何会让滤波器过度自信

若“轮速位置”和另一条“融合位置”都由同一编码器积分产生，二者误差相关。把它们当两次独立测量，会重复使用同一信息，P变小却没有对应新增证据。配置观测前写清原始数据来源、是否已融合、参考系及时间戳。

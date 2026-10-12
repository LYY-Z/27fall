#include "robot.h"


IKparam IKParam;
// 左腿相关运动学基本参数
motionControlParams LeftMotionControlParams;
// 右腿相关运动学基本参数
motionControlParams RightMotionControlParams;
motorsparam motorsParam;

float nowLefty = 0;
float nowRighty = 0;
float nowLeftx = 0;
float nowRightx = 0;
float roll_kp = 0.0025, roll_kd = -0.007; // 机器人自稳Kp、Kd值
uint32_t last_time = 0;
float radius = 0.07;
float position = 0; // 累计位移，初始为0
// 轮毂
float K1Right = 0;
float K2Right = 0;
float K3Right = 0;
float K4Right = 0;

float K1Left = 0;
float K2Left = 0;
float K3Left = 0;
float K4Left = 0;
float Ky = 1; // 0.8
float Dy = 0; // 2
Node LeftPosFK;
Node RightPosFK;
int speed_limit = 3; // 轮毂电机速度限制
float motor1_target_vel = 0, motor2_target_vel = 0;
float wheel_motor1_target = 0, wheel_motor2_target = 0; // 电机目标值
float leftY = 140, rightY = 140;                        // 机器人Y轴方向腿部高度
float leftX = 60, rightX = 60;                          // 机器人X轴方向腿部高度
int remoteHeight = 0;
int lastremoteHeight = 0;
float roll_EH;
float forwardBackward = 0;
float motor1_vel, motor2_vel;
int EH = 0;
float Tartget_Roll_angle;
float roll, pitch, yaw, init_pitch; // 陀螺仪xyz轴值
float gyroX, gyroY, gyroZ;          // 陀螺仪xyz轴加速度值
float target_roll = 0.0;
float steering = 0;
float remoteBalanceOffset = 0;
uint8_t origin_pos_flag = 1;
MIT devicesState[8];
float robot_kp = 5.0; // 3
float jump_vlaue;     // 起跳高度
float balance_offset = 2;
float kpHeight = 0.3; //0.6
float startHeight = 140;

// 限幅函数
float clampToRange(float value, float minVal, float maxVal)
{
  if (value < minVal)
    return minVal;
  if (value > maxVal)
    return maxVal;
  return value;
}

// 位移计算
float updatePosition()
{
  uint32_t now = micros();
  if (last_time == 0)
  {
    last_time = now;
  }
  float delta_t = (now - last_time) * 1e-6f;
  last_time = now;
  float v = -(motor1_vel * radius + motor2_vel * radius) / 2;
  position += v * delta_t;
  float POS_MAX = 0.1; // 10 cm
  if (position > POS_MAX)
    position = POS_MAX;
  if (position < -POS_MAX)
    position = -POS_MAX;
  return position; // 单位m
}

float calc_K1(float h) { return 0.000652 * h * h - 0.207928 * h + 1.964124; }
float calc_K2(float h) { return 0.000045 * h * h - 0.027259 * h + 1.626482; }
float calc_K3(float h) { return -0.000000 * h * h + 0.000000 * h + -0.000000; }
float calc_K4(float h) { return 0.000006 * h * h - 0.003406 * h - 4.027118; }



// 底部轮子霍尔电机控制函数 vmc
void wheel_control(float joyStick, Node *RightPosFK, Node *LeftPosFK)
{
  float vel, targetHeight;
  updatePosition();
  targetHeight = joyStick;

  K1Right = calc_K1(RightPosFK->y);
  K2Right = calc_K2(RightPosFK->y);
  K3Right = calc_K3(RightPosFK->y);
  K4Right = calc_K4(RightPosFK->y);

  K1Left = calc_K1(LeftPosFK->y);
  K2Left = calc_K2(LeftPosFK->y);
  K3Left = calc_K3(LeftPosFK->y);
  K4Left = calc_K4(LeftPosFK->y);

  vel = -((motor1_vel * radius + motor2_vel * radius) / 2);

  wheel_motor1_target = clampToRange(-(K1Right * (pitch)*PI / 180 + K2Right * (gyroY)*PI / 180 + K3Right * position + K4Right * vel) - 0.3 * steering - 0.1 * forwardBackward, -speed_limit, speed_limit);
  wheel_motor2_target = clampToRange(-(K1Left * (pitch)*PI / 180 + K2Left * (gyroY)*PI / 180 + K3Left * position + K4Left * vel) + 0.3 * steering - 0.1 * forwardBackward, -speed_limit, speed_limit);
}

void snake_case()
{
  if (Shake_shoulder == 1)
  {
    remoteHeight = 40;
    Shake_shoulder_vakue = filteredPPMValues[4];
    if (Shake_shoulder_vakue < 1600 && Shake_shoulder_vakue > 1400)
      Shake_shoulder_vakue = 1500;
    Shake_shoulder_vakue = (Shake_shoulder_vakue - 1500) / 20;
  }
  else
  {
    Shake_shoulder_vakue = 0;
  }
}

void calRightVMC(Node *RightPosFK, JointAngles *jointAngles)
{
  float j11, j12, j21, j22, theta2, Fx, Fy1, fBalance, fHeight, targetX, vel, targetHeight, heightVel, xVel;
  float kpX = 0.4;
  float kdX = 0.05;
  float kdHeight = 0.06;
  float ydot = 0.0;
  float xdot = 0.0;
  float fG = 25;//重力前馈
  fBalance = roll_EH;

  footRightVelocity(&xdot, &ydot, jointAngles, devicesState[0].vel, devicesState[2].vel);
  forwardKinematicsRight(RightPosFK, jointAngles);

  
  nowRighty = RightPosFK->y;
  targetHeight = startHeight + remoteHeight;
  targetHeight = targetHeight + jump_vlaue - Shake_shoulder_vakue;
  fHeight = kpHeight * (targetHeight - nowRighty);
  heightVel = kdHeight * ydot;
  Fy1 = fHeight + fBalance;
  Fy1 = Fy1- heightVel + fG;//阻尼+重力前馈


  nowRightx = RightPosFK->x;
  vel = -0.8 * (motor1_vel + (motor2_vel)) / 2;
  targetX = 50 - 3 * (forwardBackward - vel);
  xVel = kdX * xdot;
  Fx = kpX * (targetX - nowRightx) - xVel;

  
  theta2 = acos((RightPosFK->x - (L5 + L4 * cos(jointAngles->betaRight))) / L3);
  j11 = (L1 * sin(theta2) * sin(jointAngles->alphaRight - jointAngles->thetaRight1)) / sin(jointAngles->thetaRight1 - theta2);
  j12 = (L4 * sin(jointAngles->thetaRight1) * sin(theta2 - jointAngles->betaRight)) / sin(jointAngles->thetaRight1 - theta2);
  j21 = -(L1 * cos(theta2) * sin(jointAngles->alphaRight - jointAngles->thetaRight1)) / sin(jointAngles->thetaRight1 - theta2);
  j22 = -(L4 * cos(jointAngles->thetaRight1) * sin(theta2 - jointAngles->betaRight)) / sin(jointAngles->thetaRight1 - theta2);

  RightPosFK->backTorque = start * (1 * (1 * j11 * Fx + j21 * Fy1)) / 1000.0f;
  RightPosFK->frontTorque = start * (1 * (1 * j12 * Fx + j22 * Fy1)) / 1000.0f;
  
}

void calLeftVMC(Node *LeftPosFK, JointAngles *jointAngles)
{
  float j11, j12, j21, j22, theta2, Fx, Fy2, fBalance, fHeight, targetX, vel, targetHeight, heightVel, xVel;
  float kpX = 0.4;
  float kdX = 0.05;
  float kdHeight = 0.06;//0.08    
  float ydot = 0.0;
  float xdot = 0.0;
  float fG = 25;//重力前馈
  fBalance = -roll_EH;

  footLeftVelocity(&xdot, &ydot, jointAngles, devicesState[3].vel, devicesState[1].vel);
  forwardKinematicsLeft(LeftPosFK, jointAngles);


  nowLefty = LeftPosFK->y;
  targetHeight = startHeight + remoteHeight;
  targetHeight = targetHeight + jump_vlaue - Shake_shoulder_vakue;
  fHeight = kpHeight * (targetHeight - nowLefty);
  heightVel = kdHeight * ydot;
  Fy2 = fHeight + fBalance;
  Fy2 = Fy2- heightVel + fG;//阻尼+重力前馈

  nowLeftx = LeftPosFK->x;
  vel = -0.8 * (motor1_vel + (motor2_vel)) / 2;
  targetX = 50 + 3 * (forwardBackward - vel);
  xVel = kdX * xdot;
  Fx = kpX * (targetX - nowLeftx) - xVel;

  theta2 = acos((LeftPosFK->x - (L5 + L4 * cos(jointAngles->betaLeft))) / L3);
  j11 = (L1 * sin(theta2) * sin(jointAngles->alphaLeft - jointAngles->thetaLeft1)) / sin(jointAngles->thetaLeft1 - theta2);
  j12 = (L4 * sin(jointAngles->thetaLeft1) * sin(theta2 - jointAngles->betaLeft)) / sin(jointAngles->thetaLeft1 - theta2);
  j21 = -(L1 * cos(theta2) * sin(jointAngles->alphaLeft - jointAngles->thetaLeft1)) / sin(jointAngles->thetaLeft1 - theta2);
  j22 = -(L4 * cos(jointAngles->thetaLeft1) * sin(theta2 - jointAngles->betaLeft)) / sin(jointAngles->thetaLeft1 - theta2);

  LeftPosFK->frontTorque = start * (1 * (j11 * Fx + j21 * Fy2)) / 1000.0f;
  LeftPosFK->backTorque = start * (1 * (j12 * Fx + j22 * Fy2)) / 1000.0f;


}

// 用于获取电机初始位置函数
void get_origin_pos()
{
  if (origin_pos_flag == 1)
  {
    // 左腿关节电机初始位置
    motorsParam.motorleftsita0_origin = -devicesState[0].pos;
    motorsParam.motorleftsita1_origin = -devicesState[1].pos;

    // 右腿关节电机初始位置
    motorsParam.motorrightsita0_origin = -devicesState[3].pos;
    motorsParam.motorrightsita1_origin = -devicesState[2].pos;

    if (motorsParam.motorleftsita0_origin != 0 && motorsParam.motorleftsita1_origin != 0 && motorsParam.motorrightsita0_origin != 0 && motorsParam.motorrightsita1_origin != 0)
      origin_pos_flag = 0;
  }
}

void jump_control()
{
  static unsigned long startMillis = 0; // 用于记录起始时间
  static bool timingStarted = false;    // 标志是否开始计时
  if (jump_flag == 1)                   // 起跳flag
  {
    if (!timingStarted)
    {
      // 开始计时
      startMillis = millis();
      timingStarted = true;
    }
    if (millis() - startMillis >= 90)
    { // 判断是否达到100ms
      Ky = 0.8;
      jump_vlaue = 0;
    }
    else
    {
      Ky = 1;
      jump_vlaue = 250;
    }
  }
  else
  {
    // 重置计时器和标志位
    Ky = 0.8;
    timingStarted = false;
    startMillis = 0;
  }
}

// 轮足机器人控制部分程序
// int aaa = 0;
int Shake_shoulder_vakue = 0;

int mapJoystickValuerollzeparam(int inputValue)
{
  if (inputValue < 1000)
    inputValue = 1000;
  if (inputValue > 2000)
    inputValue = 2000;

  int output = ((inputValue - 1500) / 20);

  return output;
}

float mapJoystickValuevel(int inputValue)
{
  if (inputValue < 1000)
    inputValue = 1000;
  if (inputValue > 2000)
    inputValue = 2000;
  if (inputValue < 1600 && inputValue > 1400)
    inputValue = 1500;
  float mappedValue = (inputValue - 1500) / 100.0;
  return mappedValue;
}

// 摇杆轴数据的映射处理
float mapJoystickValueInt(int inputValue)
{
  if (inputValue < 1000)
    inputValue = 1000;
  if (inputValue > 2000)
    inputValue = 2000;
  float mappedValue = (inputValue - 1500) / 100.0;
  if (mappedValue > -0.7 && mappedValue < 0.7)
  {
    mappedValue = 0;
  }
  return mappedValue;
}
float mapJoystickValuesteering(int inputValue)
{
  if (inputValue < 1000)
    inputValue = 1000;
  if (inputValue > 2000)
    inputValue = 2000;
  if (inputValue < 1600 && inputValue > 1400)
    inputValue = 1500;
  float mappedValue = (inputValue - 1500) / 2.0;
  return mappedValue;
}
// 步态变化函数 用于前后移动模仿人滑动前行 通过遥控器控制
int trot(int inputValue)
{
  if (inputValue < 1000)
    inputValue = 1000;
  if (inputValue > 2000)
    inputValue = 2000;
  if (inputValue > 1400 && inputValue < 1550)
    inputValue = 1500;
  int output = ((inputValue - 1500) / 10);
  return output;
}

void mapPPMToRobotControl()
{
  float rollError, rollbalance;
  float rollKp = 1.5;
  float gyroKp = 0.13;
  static float last_roll_EH = 0;
  static float center_offset = 0;
  if (Shake_shoulder == 0)
  {

    // 这里用于控制腿部高度变化控制 采用增量式PID是为了让腿部快速变化时，保持稳定
    float error = (1000 - (filteredPPMValues[0] - 70)) / 1.5; // 计算误差
    remoteHeight = -0.30 * error;                             // 计算当前的值
    remoteHeight = constrainValue(remoteHeight, 0, 150);
    remoteHeight = remoteHeight + (remoteHeight - lastremoteHeight) * 0.05; // 基于误差更新输出（增量控制）
    lastremoteHeight = remoteHeight;

  } // 存储当前值作为下一次计算的参考
  // 用于roll轴自稳
  if (EH_rollflag == 1) // 自稳开关
  {
    if (abs(target_roll - roll) < 20)
    {
      center_offset += 0.0005 * (target_roll - roll);
    }
    else
    {
      center_offset *= 0.99;
    }
    center_offset = constrainValue(center_offset, -50, 50);
    rollError = target_roll - roll;
    rollbalance = gyroKp * ((rollKp * rollError) - gyroX - 0.3) + center_offset;
  }
  else
  {
    rollbalance = 0;
  }
  // 用于控制前进后退
  forwardBackward = mapJoystickValuevel(filteredPPMValues[1]);
  // 用于调节重心偏置
  remoteBalanceOffset = mapJoystickValueInt(filteredPPMValues[2]);
  // 用于控制转向
  steering = -0.03 * (-mapJoystickValuesteering(filteredPPMValues[5]) - gyroZ);
  steering = constrainValue(steering, -10, 10);

  roll_EH = sin((rollbalance * 3.14) / 180) * (LeftMotionControlParams.robotl) / 2;
  roll_EH = constrainValue(roll_EH, -80, 80);
  roll_EH = lowPassFilter(roll_EH, last_roll_EH, 0.8);  
  last_roll_EH = roll_EH;
  // Serial.print(gyroX);
  // Serial.print(",");
  // Serial.print(roll);
  // Serial.print(",");
  // Serial.println(rollbalance);
}

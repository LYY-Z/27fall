#ifndef ROBOT_H
#define ROBOT_H

#include "Kinematics/Kinematics.h"
#include "Arduino.h"
#include "bipedal_data.h"
#include "CAN_comm.h"
#include "can.h"
#include "ppm.h"

extern float robot_kp;
extern float roll_kp , roll_kd;
extern float steering ;
extern float remoteBalanceOffset;
extern int Shake_shoulder_vakue;
extern float leftY , rightY ;
extern float leftX , rightX ;
// 遥控器控制参数
extern float forwardBackward ;
// 轮足中两个轮毂电机的轮速
extern float motor1_vel, motor2_vel;
// 陀螺仪读取参数
extern float roll, pitch, yaw, init_pitch;
extern float gyroX, gyroY, gyroZ;
extern float balance_offset;
extern int remoteHeight; //腿高变化
extern float roll_EH;
extern float motorPos1 ;
extern float motorPos2 ;
extern float motorPos3 ;
extern float motorPos4 ;
extern Node LeftPosFK;
extern Node RightPosFK;
extern float wheel_motor1_target, wheel_motor2_target; // 电机目标值
extern int speed_limit; //轮毂电机速度限制
extern float jump_vlaue;
extern float kpHeight;

void jump_control();
float constrainValue(float value, float minValue, float maxValue);
int mapJoystickValuerollzeparam(int inputValue);
float mapJoystickValuevel(int inputValue);
float mapJoystickValueInt(int inputValue);
float mapJoystickValuesteering(int inputValue);
int trot(int inputValue);
void get_origin_pos();
void wheel_control(float joyStick,Node * RightPosFK,Node * LeftPosFK);
void calRightVMC(Node * RightPosFK, JointAngles * jointAngles);
void calLeftVMC(Node * LeftPosFK, JointAngles * jointAngles);
float clampToRange(float value, float minVal, float maxVal);
void mapPPMToRobotControl();
void snake_case();
#endif
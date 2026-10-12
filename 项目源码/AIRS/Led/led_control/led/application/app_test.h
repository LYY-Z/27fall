#ifndef __APP_TEST_H
#define __APP_TEST_H

#include "main.h"

/**
 * @brief 测试所有LED效果
 * 依次测试：常亮 → 呼吸 → 流水 → 跑马灯 → 彩虹
 * 完整测试约41秒，包含串口进度反馈
 */
void App_Test_AllEffects(void);

/**
 * @brief 快速效果演示
 * 35秒完整演示：常亮(5s) → 呼吸(6s) → 流水(6s) → 跑马灯(6s) → 彩虹(8s)
 */
void App_Test_QuickDemo(void);

/**
 * @brief 串口发送测试
 * 向串口发送 "STM32 LED Driver: UART Test OK\r\n"
 * @param huart 串口句柄指针
 */
void App_Test_UART_Send(UART_HandleTypeDef *huart);

/**
 * @brief 模拟协议指令测试
 * 模拟接收到一条 "设置胸口为红色呼吸灯" 的指令
 */
void App_Test_Simulate_Protocol(void);

#endif // __APP_TEST_H


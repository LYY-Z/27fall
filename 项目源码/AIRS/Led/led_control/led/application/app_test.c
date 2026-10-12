#include "app_test.h"
#include "bsp_led.h"
#include "app_comm.h"
#include "app_led_effect.h"
#include <string.h>
#include <stdio.h>

// 测试颜色定义
static const RGB_Color_t TEST_COLORS[] = {
    {255,   0,   0},   // 红色
    {  0, 255,   0},   // 绿色  
    {  0,   0, 255},   // 蓝色
    {255, 255, 255},   // 白色
};

/**
 * @brief 测试所有LED效果
 */
void App_Test_AllEffects(void) {
    char msg[64];
    
    // 发送开始测试消息
    const char* start_msg = "=== LED Effects Test Start ===\r\n";
    HAL_UART_Transmit(&huart1, (uint8_t*)start_msg, strlen(start_msg), 100);
    
    // 1. 常亮效果测试
    HAL_UART_Transmit(&huart1, (uint8_t*)"Test 1: Solid Colors\r\n", 22, 100);
    
    // 胸口-红, 左臂-绿, 右臂-蓝, 底盘-白
    for (int region = 0; region < 4; region++) {
        App_LED_SetEffect((LedRegion_t)region, EFFECT_SOLID, TEST_COLORS[region], 50);
    }
    App_LED_Effect_Process();
    
    HAL_Delay(5000); // 显示5秒
    
    // 2. 呼吸效果测试  
    HAL_UART_Transmit(&huart1, (uint8_t*)"Test 2: Breathing Effect\r\n", 26, 100);
    
    // 所有区域红色呼吸
    for (int region = 0; region < 4; region++) {
        App_LED_SetEffect((LedRegion_t)region, EFFECT_BREATHING, TEST_COLORS[0], 30);
    }
    
    // 运行呼吸效果10秒
    for (int i = 0; i < 100; i++) {
        App_LED_Effect_Process();
        HAL_Delay(100);
        
        // 每2秒报告一次进度
        if (i % 20 == 0) {
            snprintf(msg, sizeof(msg), "Breathing progress: %d%%\r\n", i);
            HAL_UART_Transmit(&huart1, (uint8_t*)msg, strlen(msg), 100);
        }
    }
    
    // 3. 流水效果测试
    HAL_UART_Transmit(&huart1, (uint8_t*)"Test 3: Flowing Effect\r\n", 24, 100);
    
    // 所有区域绿色流水
    for (int region = 0; region < 4; region++) {
        App_LED_SetEffect((LedRegion_t)region, EFFECT_FLOWING, TEST_COLORS[1], 40);
    }
    
    // 运行流水效果8秒
    for (int i = 0; i < 80; i++) {
        App_LED_Effect_Process();
        HAL_Delay(100);
        
        if (i % 20 == 0) {
            snprintf(msg, sizeof(msg), "Flowing progress: %d%%\r\n", i*100/80);
            HAL_UART_Transmit(&huart1, (uint8_t*)msg, strlen(msg), 100);
        }
    }
    
    // 4. 跑马灯效果测试
    HAL_UART_Transmit(&huart1, (uint8_t*)"Test 4: Marquee Effect\r\n", 24, 100);
    
    // 所有区域蓝色跑马灯
    for (int region = 0; region < 4; region++) {
        App_LED_SetEffect((LedRegion_t)region, EFFECT_MARQUEE, TEST_COLORS[2], 60);
    }
    
    // 运行跑马灯效果8秒
    for (int i = 0; i < 80; i++) {
        App_LED_Effect_Process();
        HAL_Delay(100);
        
        if (i % 20 == 0) {
            snprintf(msg, sizeof(msg), "Marquee progress: %d%%\r\n", i*100/80);
            HAL_UART_Transmit(&huart1, (uint8_t*)msg, strlen(msg), 100);
        }
    }
    
    // 5. 彩虹效果测试
    HAL_UART_Transmit(&huart1, (uint8_t*)"Test 5: Rainbow Effect\r\n", 24, 100);
    
    // 所有区域彩虹效果
    RGB_Color_t dummy = {0, 0, 0};
    for (int region = 0; region < 4; region++) {
        App_LED_SetEffect((LedRegion_t)region, EFFECT_RAINBOW, dummy, 50);
    }
    
    // 运行彩虹效果10秒
    for (int i = 0; i < 100; i++) {
        App_LED_Effect_Process();
        HAL_Delay(100);
        
        if (i % 25 == 0) {
            snprintf(msg, sizeof(msg), "Rainbow progress: %d%%\r\n", i);
            HAL_UART_Transmit(&huart1, (uint8_t*)msg, strlen(msg), 100);
        }
    }
    
    // 6. 关闭所有LED
    HAL_UART_Transmit(&huart1, (uint8_t*)"Test 6: Turn Off All LEDs\r\n", 27, 100);
    
    for (int region = 0; region < 4; region++) {
        App_LED_SetEffect((LedRegion_t)region, EFFECT_OFF, dummy, 0);
    }
    App_LED_Effect_Process();
    
    // 发送测试完成消息
    const char* end_msg = "=== LED Effects Test Complete ===\r\n";
    HAL_UART_Transmit(&huart1, (uint8_t*)end_msg, strlen(end_msg), 100);
}

/**
 * @brief 快速效果演示（35秒完整演示）
 */
void App_Test_QuickDemo(void) {
    const char* demo_msg = "=== Quick Demo Start (35s) ===\r\n";
    HAL_UART_Transmit(&huart1, (uint8_t*)demo_msg, strlen(demo_msg), 100);
    
    RGB_Color_t dummy = {0, 0, 0};
    
    // 1. 常亮 - 5秒
    HAL_UART_Transmit(&huart1, (uint8_t*)"Solid Colors - 5s\r\n", 19, 100);
    for (int region = 0; region < 4; region++) {
        App_LED_SetEffect((LedRegion_t)region, EFFECT_SOLID, TEST_COLORS[region], 50);
    }
    App_LED_Effect_Process();
    HAL_Delay(5000);
    
    // 2. 呼吸 - 6秒
    HAL_UART_Transmit(&huart1, (uint8_t*)"Breathing - 6s\r\n", 16, 100);
    for (int region = 0; region < 4; region++) {
        App_LED_SetEffect((LedRegion_t)region, EFFECT_BREATHING, TEST_COLORS[0], 30);
    }
    for (int i = 0; i < 60; i++) {
        App_LED_Effect_Process();
        HAL_Delay(100);
    }
    
    // 3. 流水 - 6秒
    HAL_UART_Transmit(&huart1, (uint8_t*)"Flowing - 6s\r\n", 14, 100);
    for (int region = 0; region < 4; region++) {
        App_LED_SetEffect((LedRegion_t)region, EFFECT_FLOWING, TEST_COLORS[1], 40);
    }
    for (int i = 0; i < 60; i++) {
        App_LED_Effect_Process();
        HAL_Delay(100);
    }
    
    // 4. 跑马灯 - 6秒
    HAL_UART_Transmit(&huart1, (uint8_t*)"Marquee - 6s\r\n", 14, 100);
    for (int region = 0; region < 4; region++) {
        App_LED_SetEffect((LedRegion_t)region, EFFECT_MARQUEE, TEST_COLORS[2], 60);
    }
    for (int i = 0; i < 60; i++) {
        App_LED_Effect_Process();
        HAL_Delay(100);
    }
    
    // 5. 彩虹 - 8秒
    HAL_UART_Transmit(&huart1, (uint8_t*)"Rainbow - 8s\r\n", 14, 100);
    for (int region = 0; region < 4; region++) {
        App_LED_SetEffect((LedRegion_t)region, EFFECT_RAINBOW, dummy, 50);
    }
    for (int i = 0; i < 80; i++) {
        App_LED_Effect_Process();
        HAL_Delay(100);
    }
    
    // 关闭
    for (int region = 0; region < 4; region++) {
        App_LED_SetEffect((LedRegion_t)region, EFFECT_OFF, dummy, 0);
    }
    App_LED_Effect_Process();
    
    HAL_UART_Transmit(&huart1, (uint8_t*)"=== Quick Demo Complete ===\r\n", 29, 100);
}

/**
 * @brief 串口发送测试
 */
void App_Test_UART_Send(UART_HandleTypeDef *huart) {
    const char* msg = "STM32 LED Driver: UART Test OK\r\n";
    HAL_UART_Transmit(huart, (uint8_t*)msg, strlen(msg), 100);
}

/**
 * @brief 模拟协议指令测试
 */
void App_Test_Simulate_Protocol(void) {
    // 设置胸口为红色呼吸灯
    uint8_t test_packet[] = {0xAA, 0x55, 0x03, 0x06, 0x00, 0x02, 0x32, 0xFF, 0x00, 0x00, 0x36};
    
    for(int i=0; i<sizeof(test_packet); i++) {
        App_Comm_RxHandler(test_packet[i]);
    }
    
    HAL_UART_Transmit(&huart1, (uint8_t*)"Protocol simulation sent\r\n", 26, 100);
}

#ifndef __BSP_LED_H
#define __BSP_LED_H

#include <stdint.h>
#include "main.h"
#include "usart.h"

// 外部声明定时器句柄
extern TIM_HandleTypeDef htim1;
extern TIM_HandleTypeDef htim3;

// ==========================================
// 时序参数
// ==========================================
#define WS2812_PWM_BIT_1    61  // 1码: 850ns 
#define WS2812_PWM_BIT_0    28  // 0码: 400ns
#define RESET_SLOTS         50  // 复位信号长度

// ==========================================
// LED数量定义
// ==========================================
#define LED_COUNT_CHEST     24
#define LED_COUNT_L_ARM     11  
#define LED_COUNT_R_ARM     11
#define LED_COUNT_CHASSIS   24

// 区域LED总数
#define BODY_LED_COUNT      (LED_COUNT_CHEST + LED_COUNT_L_ARM + LED_COUNT_R_ARM)  // 46
#define CHASSIS_LED_COUNT   (LED_COUNT_CHASSIS)  // 24

// ==========================================
// 缓冲区大小计算
// ==========================================
#define BITS_PER_LED        24
#define BODY_BUFFER_SIZE    (50 + BODY_LED_COUNT * BITS_PER_LED + 50)    // 50+1104+50=1204
#define CHASSIS_BUFFER_SIZE (50 + CHASSIS_LED_COUNT * BITS_PER_LED + 50) // 50+576+50=676

// ==========================================
// 区域枚举
// ==========================================
typedef enum {
    REGION_CHEST = 0,
    REGION_LEFT_ARM,
    REGION_RIGHT_ARM, 
    REGION_CHASSIS,
    REGION_ALL = 0xFF
} LedRegion_t;

// ==========================================
// 颜色结构体
// ==========================================
typedef struct {
    uint8_t R;
    uint8_t G;
    uint8_t B;
} RGB_Color_t;

// ==========================================
// DMA缓冲区结构体
// ==========================================
typedef struct {
    uint8_t StartData[50];                    // 50个0等待PWM稳定
    uint8_t ColorData[BODY_LED_COUNT * 24];   // 实际颜色数据
    uint8_t EndData[50];                      // 结束位为0
} BodyBufferStruct_t;

typedef struct {
    uint8_t StartData[50];                    // 50个0等待PWM稳定  
    uint8_t ColorData[CHASSIS_LED_COUNT * 24]; // 实际颜色数据
    uint8_t EndData[50];                      // 结束位为0
} ChassisBufferStruct_t;

// ==========================================
// 函数声明
// ==========================================
void BSP_LED_Init(void);
void BSP_LED_SetPixel(LedRegion_t region, uint16_t index, uint8_t r, uint8_t g, uint8_t b);
void BSP_LED_SetPixel_RGB(LedRegion_t region, uint16_t index, RGB_Color_t color);
void BSP_LED_ClearAll(void);
void BSP_LED_Show(void);
void BSP_LED_VerifyBuffers(UART_HandleTypeDef *huart);

#endif // __BSP_LED_H

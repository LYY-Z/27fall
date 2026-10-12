#ifndef __APP_LED_EFFECT_H
#define __APP_LED_EFFECT_H

#include "bsp_led.h"

// ==========================================
// 效果枚举
// ==========================================
typedef enum {
    EFFECT_OFF = 0,
    EFFECT_SOLID,       // 常亮
    EFFECT_BREATHING,   // 呼吸
    EFFECT_FLOWING,     // 流水
    EFFECT_MARQUEE,     // 跑马灯
    EFFECT_RAINBOW,     // 彩虹
    EFFECT_CUSTOM = 0xFF // 自定义 (ROS直接控制)
} EffectMode_t;

// ==========================================
// 效果状态结构体
// ==========================================
typedef struct {
    EffectMode_t mode;
    RGB_Color_t color;      // 基础颜色
    uint8_t speed;          // 速度 (0-100)
    uint32_t tick;          // 内部计数器
    uint8_t step;           // 内部状态步进
} RegionEffect_t;

// ==========================================
// 函数声明
// ==========================================

/**
 * @brief 初始化效果模块
 */
void App_LED_Effect_Init(void);

/**
 * @brief 设置指定区域的效果
 * @param region 区域
 * @param mode 模式
 * @param color 颜色
 * @param speed 速度
 */
void App_LED_SetEffect(LedRegion_t region, EffectMode_t mode, RGB_Color_t color, uint8_t speed);

/**
 * @brief 效果处理主循环 (需定期调用，例如每10ms)
 */
void App_LED_Effect_Process(void);

#endif // __APP_LED_EFFECT_H

#include "app_led_effect.h"
#include <math.h>
#include <stdlib.h>

// ==========================================
// 变量定义
// ==========================================
RegionEffect_t EffectStates[4]; // 对应 4 个区域: Chest, LeftArm, RightArm, Chassis

// ==========================================
// 辅助函数
// ==========================================

// HSV 转 RGB
static RGB_Color_t HSV2RGB(uint8_t h, uint8_t s, uint8_t v) {
    RGB_Color_t rgb;
    uint8_t region, remainder, p, q, t;

    if (s == 0) {
        rgb.R = v;
        rgb.G = v;
        rgb.B = v;
        return rgb;
    }

    region = h / 43;
    remainder = (h - (region * 43)) * 6;

    p = (v * (255 - s)) >> 8;
    q = (v * (255 - ((s * remainder) >> 8))) >> 8;
    t = (v * (255 - ((s * (255 - remainder)) >> 8))) >> 8;

    switch (region) {
        case 0: rgb.R = v; rgb.G = t; rgb.B = p; break;
        case 1: rgb.R = q; rgb.G = v; rgb.B = p; break;
        case 2: rgb.R = p; rgb.G = v; rgb.B = t; break;
        case 3: rgb.R = p; rgb.G = q; rgb.B = v; break;
        case 4: rgb.R = t; rgb.G = p; rgb.B = v; break;
        default: rgb.R = v; rgb.G = p; rgb.B = q; break;
    }
    return rgb;
}

// 获取区域LED数量
static uint16_t GetRegionLedCount(LedRegion_t region) {
    switch (region) {
        case REGION_CHEST: return LED_COUNT_CHEST;
        case REGION_LEFT_ARM: return LED_COUNT_L_ARM;
        case REGION_RIGHT_ARM: return LED_COUNT_R_ARM;
        case REGION_CHASSIS: return LED_COUNT_CHASSIS;
        default: return 0;
    }
}

// ==========================================
// 效果实现函数
// ==========================================

// 实现呼吸效果，速度范围0-100
static void Run_Breathing(LedRegion_t region, RegionEffect_t* state) {
    // 将速度0-100映射到合适的呼吸频率
    float speed_factor = 0.02f + (state->speed * 0.08f / 100.0f); // 0.02-0.1的范围
    float angle = (float)state->tick * speed_factor;
    uint8_t brightness = (sin(angle) + 1.0f) * 127.0f;

    uint16_t count = GetRegionLedCount(region);
    for (uint16_t i = 0; i < count; i++) {
        BSP_LED_SetPixel(region, i, 
            (state->color.R * brightness) >> 8,
            (state->color.G * brightness) >> 8,
            (state->color.B * brightness) >> 8
        );
    }
}

// 实现流水灯效果，速度范围0-100
static void Run_Flowing(LedRegion_t region, RegionEffect_t* state) {
    uint16_t count = GetRegionLedCount(region);
    
    // 速度0-100映射到移动间隔：10-1（值越小移动越快）
    uint16_t speed_factor = 10 - (state->speed * 9 / 100); // 10-1的范围
    if (speed_factor < 1) speed_factor = 1; // 确保最小值为1
    
    uint16_t pos = (state->tick / speed_factor) % count;
    
    for (uint16_t i = 0; i < count; i++) {
        if (i == pos) {
            BSP_LED_SetPixel_RGB(region, i, state->color);
        } else {
            BSP_LED_SetPixel(region, i, 0, 0, 0);
        }
    }
}

// 实现跑马灯效果，速度范围0-100
static void Run_Marquee(LedRegion_t region, RegionEffect_t* state) {
    uint16_t count = GetRegionLedCount(region);
    uint16_t speed_factor = 25 - (state->speed * 20 / 100);
    uint16_t offset = (state->tick / speed_factor) % count;
    
    uint8_t group_size = 5;    // 更多亮的LED
    uint8_t gap_size = 1;      // 更小的间隔
    
    for (uint16_t i = 0; i < count; i++) {
        uint16_t rel_pos = (i + count - offset) % count;
        uint16_t group_index = rel_pos % (group_size + gap_size);
        
        if (group_index < group_size) {
            BSP_LED_SetPixel_RGB(region, i, state->color);
        } else {
            BSP_LED_SetPixel(region, i, 0, 0, 0);
        }
    }
}

// 实现彩虹效果，速度范围0-100
static void Run_Rainbow(LedRegion_t region, RegionEffect_t* state) {
    uint16_t count = GetRegionLedCount(region);
    
    // 速度0-100映射到彩虹流动速度：1-10
    uint8_t speed_factor = 1 + (state->speed * 9 / 100); // 1-10的范围
    uint8_t hue_start = (state->tick * speed_factor) & 0xFF;
    
    for (uint16_t i = 0; i < count; i++) {
        uint8_t hue = hue_start + (i * 255 / count);
        RGB_Color_t c = HSV2RGB(hue, 255, 255);
        BSP_LED_SetPixel_RGB(region, i, c);
    }
}

// ==========================================
// 外部接口
// ==========================================

void App_LED_Effect_Init(void) {
    // 默认初始化为关闭
    for (int i = 0; i < 4; i++) {
        EffectStates[i].mode = EFFECT_OFF;
        EffectStates[i].speed = 50;
        EffectStates[i].tick = 0;
        EffectStates[i].color.R = 255; // Default Red
        EffectStates[i].color.G = 0;
        EffectStates[i].color.B = 0;
    }
}

void App_LED_SetEffect(LedRegion_t region, EffectMode_t mode, RGB_Color_t color, uint8_t speed) {
    if (region == REGION_ALL) {
        for (int i = 0; i < 4; i++) {
            EffectStates[i].mode = mode;
            EffectStates[i].color = color;
            EffectStates[i].speed = speed;
            EffectStates[i].tick = 0;
        }
    } else if (region <= REGION_CHASSIS) {
        EffectStates[region].mode = mode;
        EffectStates[region].color = color;
        EffectStates[region].speed = speed;
        EffectStates[region].tick = 0;
    }
}

void App_LED_Effect_Process(void) {
    for (int i = 0; i < 4; i++) {
        LedRegion_t region = (LedRegion_t)i;
        RegionEffect_t* state = &EffectStates[i];
        
        state->tick++;

        switch (state->mode) {
            case EFFECT_OFF:
                {
                    uint16_t count = GetRegionLedCount(region);
                    for(int k=0; k<count; k++) BSP_LED_SetPixel(region, k, 0,0,0);
                }
                break;
            case EFFECT_SOLID:
                {
                    uint16_t count = GetRegionLedCount(region);
                    for(int k=0; k<count; k++) BSP_LED_SetPixel_RGB(region, k, state->color);
                }
                break;
            case EFFECT_BREATHING:
                Run_Breathing(region, state);
                break;
            case EFFECT_FLOWING:
                Run_Flowing(region, state);
                break;
            case EFFECT_MARQUEE:    
                Run_Marquee(region, state);
                break;
            case EFFECT_RAINBOW:
                Run_Rainbow(region, state);
                break;
            case EFFECT_CUSTOM:
                // 自定义模式不做处理，颜色由外部直接设置
                break;
            default:
                break;
        }
    }
    
    // 统一刷新
    BSP_LED_Show();
}

#include "bsp_led.h"
#include <string.h>

// ==========================================
// DMA缓冲区定义
// ==========================================
BodyBufferStruct_t Body_DMA_Buffer;
ChassisBufferStruct_t Chassis_DMA_Buffer;

// 逻辑颜色缓存
RGB_Color_t Body_Pixels[BODY_LED_COUNT];
RGB_Color_t Chassis_Pixels[CHASSIS_LED_COUNT];

// ==========================================
// 内部辅助函数
// ==========================================

/**
 * @brief 将RGB颜色转换为PWM数据写入缓冲区
 */
static void Write_Color_To_Buffer(uint8_t* buffer, uint32_t index_offset, 
                                 uint8_t r, uint8_t g, uint8_t b, uint8_t format) {
    uint8_t data[3];
    
    // 根据格式确定数据顺序
    if (format == 0) { 
        // WS2815格式: GRB（胸口）
        data[0] = g;
        data[1] = r; 
        data[2] = b;
    } else { 
        // WS2812格式: RGB（手臂和底盘）
        data[0] = r;
        data[1] = g;
        data[2] = b;
    }

    // 位写入逻辑
    for(int j = 0; j < 8; j++) {
        buffer[index_offset + j]       = (data[0] & (0x80 >> j)) ? WS2812_PWM_BIT_1 : WS2812_PWM_BIT_0;  // 第一个字节
        buffer[index_offset + j + 8]   = (data[1] & (0x80 >> j)) ? WS2812_PWM_BIT_1 : WS2812_PWM_BIT_0;  // 第二个字节  
        buffer[index_offset + j + 16]  = (data[2] & (0x80 >> j)) ? WS2812_PWM_BIT_1 : WS2812_PWM_BIT_0;  // 第三个字节
    }
}

// ==========================================
// 外部接口实现
// ==========================================

void BSP_LED_Init(void) {
    // 清空DMA缓冲区
    memset(&Body_DMA_Buffer, 0, sizeof(Body_DMA_Buffer));
    memset(&Chassis_DMA_Buffer, 0, sizeof(Chassis_DMA_Buffer));
    
    // 清空逻辑颜色缓存
    memset(Body_Pixels, 0, sizeof(Body_Pixels));
    memset(Chassis_Pixels, 0, sizeof(Chassis_Pixels));
    
    // 初始化起始和结束数据为0（重要！）
    for(int i = 0; i < 50; i++) {
        Body_DMA_Buffer.StartData[i] = 0;
        Body_DMA_Buffer.EndData[i] = 0;
        Chassis_DMA_Buffer.StartData[i] = 0;
        Chassis_DMA_Buffer.EndData[i] = 0;
    }
}

void BSP_LED_SetPixel(LedRegion_t region, uint16_t index, uint8_t r, uint8_t g, uint8_t b) {
    uint16_t global_index = 0;
    uint8_t* target_buffer = NULL;
    RGB_Color_t* target_pixels = NULL;
    uint8_t is_rgb_format = 0;

    switch (region) {
        case REGION_CHEST:
            if (index >= LED_COUNT_CHEST) return;
            global_index = index; // 0-23
            target_buffer = Body_DMA_Buffer.ColorData;
            target_pixels = Body_Pixels;
            is_rgb_format = 0; // WS2815 GRB
            break;

        case REGION_LEFT_ARM:
            if (index >= LED_COUNT_L_ARM) return;
            global_index = LED_COUNT_CHEST + index; // 24-34
            target_buffer = Body_DMA_Buffer.ColorData; 
            target_pixels = Body_Pixels;
            is_rgb_format = 1; // WS2812 RGB
            break;

        case REGION_RIGHT_ARM:
            if (index >= LED_COUNT_R_ARM) return;
            global_index = LED_COUNT_CHEST + LED_COUNT_L_ARM + index; // 35-45
            target_buffer = Body_DMA_Buffer.ColorData;
            target_pixels = Body_Pixels;
            is_rgb_format = 1; // WS2812 RGB
            break;

        case REGION_CHASSIS:
            if (index >= LED_COUNT_CHASSIS) return;
            global_index = index; // 0-23
            target_buffer = Chassis_DMA_Buffer.ColorData;
            target_pixels = Chassis_Pixels;
            is_rgb_format = 1; // WS2812 RGB
            break;

        default:
            return;
    }

    // 更新逻辑颜色缓存
    target_pixels[global_index] = (RGB_Color_t){r, g, b};
    
    // 计算缓冲区偏移并写入
    uint32_t buffer_offset = global_index * 24;
    Write_Color_To_Buffer(target_buffer, buffer_offset, r, g, b, is_rgb_format);
}

void BSP_LED_SetPixel_RGB(LedRegion_t region, uint16_t index, RGB_Color_t color) {
    BSP_LED_SetPixel(region, index, color.R, color.G, color.B);
}

void BSP_LED_ClearAll(void) {
    // 快速清空所有缓冲区
    memset(Body_DMA_Buffer.ColorData, 0, sizeof(Body_DMA_Buffer.ColorData));
    memset(Chassis_DMA_Buffer.ColorData, 0, sizeof(Chassis_DMA_Buffer.ColorData));
    memset(Body_Pixels, 0, sizeof(Body_Pixels));
    memset(Chassis_Pixels, 0, sizeof(Chassis_Pixels));
}

void BSP_LED_Show(void) {
    // 身体区域
    HAL_TIM_PWM_Stop_DMA(&htim1, TIM_CHANNEL_2);
    HAL_Delay(1);
    HAL_TIM_PWM_Start_DMA(&htim1, TIM_CHANNEL_2, 
                         (uint32_t*)(&Body_DMA_Buffer), 
                         sizeof(Body_DMA_Buffer));
    
    // 底盘区域  
    HAL_TIM_PWM_Stop_DMA(&htim3, TIM_CHANNEL_1);
    HAL_Delay(1);
    HAL_TIM_PWM_Start_DMA(&htim3, TIM_CHANNEL_1,
                         (uint32_t*)(&Chassis_DMA_Buffer),
                         sizeof(Chassis_DMA_Buffer));
    
    // 等待传输完成
    HAL_Delay(3);
    
    // 停止DMA，保持PWM运行
    HAL_TIM_PWM_Stop_DMA(&htim1, TIM_CHANNEL_2);
    HAL_TIM_PWM_Stop_DMA(&htim3, TIM_CHANNEL_1);
}

void BSP_LED_VerifyBuffers(UART_HandleTypeDef *huart) {
    char msg[128];
    
    // 验证缓冲区大小
    uint32_t body_size = sizeof(Body_DMA_Buffer);
    uint32_t chassis_size = sizeof(Chassis_DMA_Buffer);
    
    printf(msg, sizeof(msg), "Body Buffer Size: %lu bytes\r\n", body_size);
    HAL_UART_Transmit(huart, (uint8_t*)msg, strlen(msg), 100);
    
    printf(msg, sizeof(msg), "Chassis Buffer Size: %lu bytes\r\n", chassis_size);
    HAL_UART_Transmit(huart, (uint8_t*)msg, strlen(msg), 100);
    
    // 验证颜色数据区大小
    uint32_t body_color_size = sizeof(Body_DMA_Buffer.ColorData);
    uint32_t chassis_color_size = sizeof(Chassis_DMA_Buffer.ColorData);
    
    printf(msg, sizeof(msg), "Body Color Data: %lu bytes (%d LEDs)\r\n", 
             body_color_size, body_color_size / 24);
    HAL_UART_Transmit(huart, (uint8_t*)msg, strlen(msg), 100);
    
    printf(msg, sizeof(msg), "Chassis Color Data: %lu bytes (%d LEDs)\r\n", 
             chassis_color_size, chassis_color_size / 24);
    HAL_UART_Transmit(huart, (uint8_t*)msg, strlen(msg), 100);
}

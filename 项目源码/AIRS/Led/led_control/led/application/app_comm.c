#include "app_comm.h"
#include "app_led_effect.h"
#include "bsp_led.h"
#include <string.h>

// ==========================================
// 协议常量定义
// ==========================================
#define FRAME_HEADER_1          0xAA    // 帧头第一个字节
#define FRAME_HEADER_2          0x55    // 帧头第二个字节
#define CMD_ACK                 0x00    // 应答命令
#define CMD_SET_EFFECT          0x01    // 设置效果命令
#define CMD_SET_COLOR           0x02    // 设置自定义颜色命令
#define CMD_SET_EFFECT_COLOR    0x03    // 设置效果+颜色命令
#define CMD_REPORT_LED          0x12    // LED状态上报命令

// ==========================================
// 状态机枚举
// ==========================================
typedef enum {
    STATE_WAIT_HEADER_1,  // 等待第一个帧头 0xAA
    STATE_WAIT_HEADER_2,  // 等待第二个帧头 0x55  
    STATE_WAIT_CMD,       // 等待命令字节
    STATE_WAIT_LEN,       // 等待数据长度字节
    STATE_WAIT_DATA,      // 等待数据载荷
    STATE_WAIT_CS         // 等待校验和
} CommState_t;

// ==========================================
// 变量定义
// ==========================================
static CommState_t rx_state = STATE_WAIT_HEADER_1;  // 当前状态机状态
static uint8_t rx_cmd = 0;                          // 当前接收的命令
static uint8_t rx_len = 0;                          // 数据长度
static uint8_t rx_data_idx = 0;                     // 数据缓冲区索引
static uint8_t rx_buffer[256];                      // 数据缓冲区
static uint8_t rx_checksum = 0;                     // 校验和累加器

// ==========================================
// 内部处理函数
// ==========================================

/**
 * @brief 发送协议帧
 * @param cmd 命令字
 * @param data 数据指针
 * @param len 数据长度
 */
static void Send_Packet(uint8_t cmd, uint8_t* data, uint8_t len) {
    uint8_t packet[256];
    uint8_t idx = 0;
    uint8_t checksum = 0;
    
    // 帧头
    packet[idx++] = FRAME_HEADER_1;
    packet[idx++] = FRAME_HEADER_2;
    
    // 命令和长度
    packet[idx++] = cmd;
    packet[idx++] = len;
    
    // 数据
    if (len > 0 && data != NULL) {
        memcpy(&packet[idx], data, len);
        idx += len;
    }
    
    // 计算校验和: CMD + LEN + DATA...
    checksum = cmd + len;
    for (int i = 0; i < len; i++) {
        checksum += data[i];
    }
    packet[idx++] = checksum;
    
    // 发送
    HAL_UART_Transmit(&huart1, packet, idx, 100);
}

/**
 * @brief 处理接收到的完整数据包
 */
static void Process_Packet(void) {
    uint8_t ack_data[2];
    uint8_t report_data[2];
    
    // 根据命令字进行不同的处理
    switch (rx_cmd) {
        case CMD_SET_EFFECT:
            // 设置效果命令：[区域, 效果ID, 速度]
            // 数据格式: | Region(1B) | EffectID(1B) | Speed(1B) |
            if (rx_len >= 3) {
                LedRegion_t region = (LedRegion_t)rx_buffer[0];  // 区域: 0-3
                EffectMode_t mode = (EffectMode_t)rx_buffer[1];  // 效果模式
                uint8_t speed = rx_buffer[2];                    // 速度参数
                
                // 使用预定义的默认颜色（白色）
                RGB_Color_t default_color = {255, 255, 255}; 
                
                // 调用效果设置函数
                App_LED_SetEffect(region, mode, default_color, speed);

                // 发送ACK
                ack_data[0] = rx_cmd;
                ack_data[1] = 0x00; // OK
                Send_Packet(CMD_ACK, ack_data, 2);
                
                // 发送状态报告
                report_data[0] = region;
                report_data[1] = mode;
                Send_Packet(CMD_REPORT_LED, report_data, 2);
            }
            break;
            
        case CMD_SET_EFFECT_COLOR:
            // 设置效果+颜色命令：[区域, 效果ID, 速度, R, G, B]
            // 数据格式: | Region(1B) | EffectID(1B) | Speed(1B) | R(1B) | G(1B) | B(1B) |
            if (rx_len >= 6) {
                LedRegion_t region = (LedRegion_t)rx_buffer[0];
                EffectMode_t mode = (EffectMode_t)rx_buffer[1];
                uint8_t speed = rx_buffer[2];
                RGB_Color_t color = {
                    .R = rx_buffer[3],
                    .G = rx_buffer[4], 
                    .B = rx_buffer[5]
                };
                
                App_LED_SetEffect(region, mode, color, speed);

                // 发送ACK
                ack_data[0] = rx_cmd;
                ack_data[1] = 0x00; // OK
                Send_Packet(CMD_ACK, ack_data, 2);
                
                // 发送状态报告
                report_data[0] = region;
                report_data[1] = mode;
                Send_Packet(CMD_REPORT_LED, report_data, 2);
            }
            break;
            
        case CMD_SET_COLOR:
            // 设置自定义颜色命令：[区域, 起始索引, LED数量, R,G,B, R,G,B...]
            // 数据格式: | Region(1B) | StartIdx(1B) | Count(1B) | RGB数据(Count*3B) |
            if (rx_len >= 3) {
                LedRegion_t region = (LedRegion_t)rx_buffer[0];  // 区域
                uint8_t start_idx = rx_buffer[1];                // 起始LED索引
                uint8_t count = rx_buffer[2];                    // LED数量
                
                // 切换到自定义模式，这样效果模块不会覆盖我们的颜色设置
                RGB_Color_t dummy = {0,0,0};
                App_LED_SetEffect(region, EFFECT_CUSTOM, dummy, 0);
                
                // 解析RGB数据并设置每个LED的颜色
                uint8_t* pColorData = &rx_buffer[3];  // RGB数据起始位置
                for (int i = 0; i < count; i++) {
                    // 安全检查，防止数组越界
                    if (3 + i*3 + 2 >= rx_len) break;
                    
                    // 提取RGB分量
                    uint8_t r = pColorData[i*3 + 0];
                    uint8_t g = pColorData[i*3 + 1];
                    uint8_t b = pColorData[i*3 + 2];
                    
                    // 设置单个LED颜色
                    BSP_LED_SetPixel(region, start_idx + i, r, g, b);
                }

                // 发送ACK
                ack_data[0] = rx_cmd;
                ack_data[1] = 0x00; // OK
                Send_Packet(CMD_ACK, ack_data, 2);
                
                // 发送状态报告
                report_data[0] = region;
                report_data[1] = EFFECT_CUSTOM;
                Send_Packet(CMD_REPORT_LED, report_data, 2);
            }
            break;

        default:
            // 未知命令，忽略
            break;
    }
}

// ==========================================
// 外部接口
// ==========================================

/**
 * @brief 串口接收字节处理函数
 * @param byte 接收到的字节
 */
void App_Comm_RxHandler(uint8_t byte) {
    switch (rx_state) {
        case STATE_WAIT_HEADER_1:
            // 等待第一个帧头
            if (byte == FRAME_HEADER_1) {
                rx_state = STATE_WAIT_HEADER_2;  // 正确，进入下一状态
            }
            break;
            
        case STATE_WAIT_HEADER_2:
            // 等待第二个帧头
            if (byte == FRAME_HEADER_2) {
                rx_state = STATE_WAIT_CMD;  // 帧头正确，等待命令
            } else {
                rx_state = STATE_WAIT_HEADER_1;  // 帧头错误，回到初始状态
            }
            break;
            
        case STATE_WAIT_CMD:
            // 接收命令字节
            rx_cmd = byte;
            rx_checksum = byte;  // 校验和从命令字节开始计算
            rx_state = STATE_WAIT_LEN;
            break;
            
        case STATE_WAIT_LEN:
            // 接收数据长度
            rx_len = byte;
            rx_checksum += byte;  // 累加到校验和
            rx_data_idx = 0;      // 重置数据索引
            
            if (rx_len > 0) {
                rx_state = STATE_WAIT_DATA;  // 有数据，进入数据接收状态
            } else {
                rx_state = STATE_WAIT_CS;    // 无数据，直接等待校验和
            }
            break;
            
        case STATE_WAIT_DATA:
            // 接收数据载荷
            rx_buffer[rx_data_idx++] = byte;
            rx_checksum += byte;  // 每个数据字节都累加到校验和
            
            if (rx_data_idx >= rx_len) {
                rx_state = STATE_WAIT_CS;  // 数据接收完成
            }
            break;
            
        case STATE_WAIT_CS:
            // 验证校验和
            if (byte == rx_checksum) {
                Process_Packet();  // 校验通过，处理数据包
            }
            // 无论校验是否通过，都回到初始状态准备接收下一帧
            rx_state = STATE_WAIT_HEADER_1;
            break;
            
        default:
            // 异常情况，重置状态机
            rx_state = STATE_WAIT_HEADER_1;
            break;
    }
}

/**
 * @brief 获取通信模块状态
 * @param state 返回当前状态机状态
 * @param cmd 返回最后接收到的命令
 * @param len 返回最后接收到的数据长度
 */
void App_Comm_GetStatus(uint8_t* state, uint8_t* cmd, uint8_t* len) {
    if (state) *state = (uint8_t)rx_state;
    if (cmd) *cmd = rx_cmd;
    if (len) *len = rx_len;
}

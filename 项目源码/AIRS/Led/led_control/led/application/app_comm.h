#ifndef __APP_COMM_H
#define __APP_COMM_H

#include <stdint.h>

/**
 * @brief 串口接收字节处理函数 (在中断中调用)
 * @param byte 接收到的字节
 */
void App_Comm_RxHandler(uint8_t byte);

/**
 * @brief 获取通信模块状态，用于测试和调试
 * @param state 返回当前状态机状态
 * @param cmd 返回最后接收到的命令
 * @param len 返回最后接收到的数据长度
 */
void App_Comm_GetStatus(uint8_t* state, uint8_t* cmd, uint8_t* len);

#endif // __APP_COMM_H



#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import rospy
import serial
import json
import threading
import time
from std_msgs.msg import String

class LedDriverNode:
    def __init__(self):
        rospy.init_node('led_driver_node', anonymous=False)

        # 获取参数
        self.port = rospy.get_param('~port', '/dev/ttyUSB0')
        self.baud = rospy.get_param('~baud', 115200)
        self.sync_arms = rospy.get_param('~sync_arms', True)  # 默认左臂控制右臂

        # 初始化串口
        try:
            self.ser = serial.Serial(self.port, self.baud, timeout=0.1)
            rospy.loginfo(f"Connected to serial port: {self.port}")
        except Exception as e:
            rospy.logerr(f"Failed to open serial port: {e}")
            exit(1)

        # 命令映射
        self.CMD_ACK = 0x00                  # 应答
        self.CMD_SET_EFFECT = 0x01           # 设置效果
        self.CMD_SET_COLOR = 0x02            # 设置自定义颜色
        self.CMD_SET_EFFECT_COLOR = 0x03     # 设置效果+颜色
        self.CMD_REPORT_LED = 0x12           # LED状态上报

        # 区域映射
        self.REGION_CHEST = 0x00
        self.REGION_LEFT_ARM = 0x01
        self.REGION_RIGHT_ARM = 0x02
        self.REGION_CHASSIS = 0x03
        self.REGION_ALL = 0xFF

        # 效果映射
        self.EFFECT_MAP = {
            "off": 0x00,
            "solid": 0x01,
            "breathing": 0x02,
            "flowing": 0x03,
            "marquee": 0x04,
            "rainbow": 0x05,
            "custom": 0xFF
        }

        # 订阅者
        rospy.Subscriber('/led_control/command', String, self.cmd_callback)
        
        # 发布者
        self.pub_led_state = rospy.Publisher('/led_control/led_state', String, queue_size=10)
        self.pub_status = rospy.Publisher('/led_control/status', String, queue_size=10)
        # 启动串口读取线程
        self.serial_thread = threading.Thread(target=self.read_serial)
        self.serial_thread.daemon = True
        self.serial_thread.start()

        rospy.loginfo("LED Driver Node Started")

    def send_packet(self, cmd, data):
        """
        发送协议帧: AA 55 CMD LEN DATA... CS
        """
        length = len(data)
        checksum = (cmd + length + sum(data)) & 0xFF
        
        packet = bytearray()
        packet.append(0xAA)
        packet.append(0x55)
        packet.append(cmd)
        packet.append(length)
        packet.extend(data)
        packet.append(checksum)
        
        try:
            self.ser.write(packet)
            # 添加小延迟确保数据发送完成
            time.sleep(0.01)
            return True
        except Exception as e:
            rospy.logerr(f"Serial write error: {e}")
            return False

    def read_serial(self):
        """读取串口数据 (纯二进制协议处理)"""
        buffer = bytearray()
        
        while not rospy.is_shutdown():
            try:
                if self.ser.in_waiting > 0:
                    buffer.extend(self.ser.read(self.ser.in_waiting))
                
                # 循环处理缓冲区中的数据
                while len(buffer) >= 5: # 最小包长: Header(2) + Cmd(1) + Len(1) + CS(1)
                    # 1. 寻找帧头 0xAA 0x55
                    if buffer[0] != 0xAA or buffer[1] != 0x55:
                        # 如果不是帧头，丢弃第一个字节，继续寻找
                        buffer.pop(0)
                        continue
                    
                    # 2. 获取数据长度
                    length = buffer[3]
                    total_len = 5 + length
                    
                    # 3. 检查缓冲区数据是否足够
                    if len(buffer) < total_len:
                        # 数据不够，跳出循环等待更多数据
                        break
                        
                    # 4. 提取完整包
                    packet = buffer[:total_len]
                    self.parse_binary_packet(packet)
                    
                    # 5. 从缓冲区移除已处理的包
                    buffer = buffer[total_len:]
                
                # 短暂休眠，避免占用过多CPU
                time.sleep(0.002)

            except Exception as e:
                rospy.logerr(f"Serial read error: {e}")
                time.sleep(1)

    def parse_binary_packet(self, packet):
        """解析二进制包"""
        cmd = packet[2]
        length = packet[3]
        data = packet[4:4+length]
        checksum = packet[-1]
        
        # 校验和验证
        calc_sum = (cmd + length + sum(data)) & 0xFF
        if calc_sum != checksum:
            rospy.logwarn(f"Checksum Error: Calc={calc_sum:02X} Recv={checksum:02X}")
            return

        if cmd == self.CMD_ACK:
            orig_cmd = data[0]
            status = data[1]
            status_str = "OK" if status == 0 else f"Error({status})"
            msg = f"ACK: Cmd=0x{orig_cmd:02X} Status={status_str}"
            
            # 终端打印
            rospy.loginfo(f"[RX] {msg}")
            # 发布状态
            self.pub_status.publish(msg)
            
        elif cmd == self.CMD_REPORT_LED:
            region = data[0]
            mode = data[1]
            
            # 区域名称映射
            region_str = "unknown"
            if region == self.REGION_CHEST: region_str = "chest"
            elif region == self.REGION_LEFT_ARM: region_str = "left_arm"
            elif region == self.REGION_RIGHT_ARM: region_str = "right_arm"
            elif region == self.REGION_CHASSIS: region_str = "chassis"
            elif region == self.REGION_ALL: region_str = "all"
            
            # 反向查找效果名称
            mode_str = "unknown"
            for name, id in self.EFFECT_MAP.items():
                if id == mode:
                    mode_str = name
                    break
            
            # 终端打印
            rospy.loginfo(f"[RX] LED Report: {region_str} Mode={mode_str}({mode})")
            
            report = {
                "region": region_str,
                "mode": mode,
                "effect": mode_str
            }
            self.pub_led_state.publish(json.dumps(report))

    def sync_right_arm(self, cmd_data, region_str):
        """同步右臂效果"""
        try:
            # 创建右臂命令数据
            right_cmd = cmd_data.copy()
            right_cmd["region"] = "right_arm"
            
            # 重新处理右臂命令
            effect_str = right_cmd.get("effect", "off")
            region_id = self.REGION_RIGHT_ARM
            
            # 解析效果
            effect_id = self.EFFECT_MAP.get(effect_str, 0x00)
            
            # 如果是custom效果
            if effect_str == "custom":
                start_index = right_cmd.get("start_index", 0)
                rgb_data = right_cmd.get("rgb_data", [])
                
                if rgb_data:
                    count = len(rgb_data) // 3
                    payload = [region_id, start_index, count]
                    payload.extend(rgb_data)
                    success = self.send_packet(self.CMD_SET_COLOR, payload)
                    
            else:
                # 设置预设效果
                speed = right_cmd.get("speed", 50)
                color = right_cmd.get("color", None)
                
                # 确保速度在0-100范围内
                speed = max(0, min(100, speed))
                
                # 根据是否有颜色选择协议
                if color and len(color) >= 3:
                    r, g, b = color[0], color[1], color[2]
                    payload = [region_id, effect_id, speed, r, g, b]
                    success = self.send_packet(self.CMD_SET_EFFECT_COLOR, payload)
                else:
                    payload = [region_id, effect_id, speed]
                    success = self.send_packet(self.CMD_SET_EFFECT, payload)
                        
        except Exception as e:
            rospy.logerr(f"Error syncing right arm: {e}")

    def cmd_callback(self, msg):
        """
        处理指令消息 - 支持所有功能
        """
        try:
            cmd_data = json.loads(msg.data)
            region_str = cmd_data.get("region", "all")
            effect_str = cmd_data.get("effect", "off")
            
            # 解析区域
            region_id = self.REGION_ALL
            if region_str == "chest": 
                region_id = self.REGION_CHEST
            elif region_str == "left_arm": 
                region_id = self.REGION_LEFT_ARM
            elif region_str == "right_arm": 
                region_id = self.REGION_RIGHT_ARM
            elif region_str == "chassis": 
                region_id = self.REGION_CHASSIS
            
            # 解析效果
            effect_id = self.EFFECT_MAP.get(effect_str, 0x00)
            
            # 如果是custom效果，使用直接设置颜色
            if effect_str == "custom":
                start_index = cmd_data.get("start_index", 0)
                rgb_data = cmd_data.get("rgb_data", [])
                
                if rgb_data:
                    count = len(rgb_data) // 3
                    payload = [region_id, start_index, count]
                    payload.extend(rgb_data)
                    success = self.send_packet(self.CMD_SET_COLOR, payload)
                    
                    # 同步处理 - 只在设置左臂时同步到右臂
                    if self.sync_arms and region_str == "left_arm" and success:
                        self.sync_right_arm(cmd_data, region_str)
                
            else:
                # 设置预设效果
                speed = cmd_data.get("speed", 50)
                color = cmd_data.get("color", None)
                
                # 确保速度在0-100范围内
                speed = max(0, min(100, speed))
                
                # 根据是否有颜色选择协议
                if color and len(color) >= 3:
                    r, g, b = color[0], color[1], color[2]
                    payload = [region_id, effect_id, speed, r, g, b]
                    success = self.send_packet(self.CMD_SET_EFFECT_COLOR, payload)
                    
                    # 同步处理 - 只在设置左臂时同步到右臂
                    if self.sync_arms and region_str == "left_arm" and success:
                        self.sync_right_arm(cmd_data, region_str)
                        
                else:
                    payload = [region_id, effect_id, speed]
                    success = self.send_packet(self.CMD_SET_EFFECT, payload)
                    
                    # 同步处理 - 只在设置左臂时同步到右臂
                    if self.sync_arms and region_str == "left_arm" and success:
                        self.sync_right_arm(cmd_data, region_str)
                
        except json.JSONDecodeError:
            rospy.logwarn("Invalid JSON command")
        except Exception as e:
            rospy.logerr(f"Error processing command: {e}")

    def run(self):
        """主运行循环"""
        rospy.loginfo("LED Driver Node is running...")
        rospy.spin()

    def __del__(self):
        """析构函数，关闭串口"""
        if hasattr(self, 'ser') and self.ser.is_open:
            self.ser.close()
            rospy.loginfo("Serial port closed")

if __name__ == '__main__':
    try:
        node = LedDriverNode()
        node.run()
    except rospy.ROSInterruptException:
        pass
    except Exception as e:
        rospy.logerr(f"Node error: {e}")
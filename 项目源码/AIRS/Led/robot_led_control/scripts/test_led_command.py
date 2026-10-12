#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import rospy
import json
from std_msgs.msg import String
import time

class LedTester:
    def __init__(self):
        rospy.init_node('led_tester', anonymous=True)
        
        # 只使用一个发布器
        self.cmd_pub = rospy.Publisher('/led_control/command', String, queue_size=10)
        
        # 等待发布器建立连接
        time.sleep(2.0)
        
    def send_command(self, region, effect, speed=50, color=None, start_index=None, rgb_data=None):
        """发送效果命令"""
        cmd = {
            "region": region,
            "effect": effect
        }
        
        # 可选参数
        if speed is not None:
            cmd["speed"] = speed
        if color is not None:
            cmd["color"] = color
        if start_index is not None:
            cmd["start_index"] = start_index
        if rgb_data is not None:
            cmd["rgb_data"] = rgb_data
            
        msg = String()
        msg.data = json.dumps(cmd)
        self.cmd_pub.publish(msg)
        rospy.loginfo(f"Sent command: {cmd}")
        
    def test_all_commands(self):
        """测试所有命令类型"""
        rospy.loginfo("=== Testing All Command Types ===")
        
        # 1. 测试效果（无颜色）
        rospy.loginfo("1. Testing effect (no color)")
        self.send_command("chest", "breathing", 30)
        time.sleep(3)
        
        # 2. 测试效果（带颜色）
        rospy.loginfo("2. Testing effect (with color)")
        self.send_command("left_arm", "flowing", 60, [0, 255, 0])
        time.sleep(3)
        
        # 3. 测试自定义颜色（从索引5开始）
        rospy.loginfo("3. Testing custom color with start index")
        rgb_data = [255, 0, 0, 0, 255, 0, 0, 0, 255]  # 红、绿、蓝
        self.send_command("chest", "custom", start_index=5, rgb_data=rgb_data)
        time.sleep(3)
        
        # 4. 测试手臂同步
        rospy.loginfo("4. Testing arm sync")
        self.send_command("left_arm", "solid", 80, [255, 255, 0])
        time.sleep(3)
        
        # 5. 测试右臂覆盖
        rospy.loginfo("5. Testing right arm override")
        self.send_command("right_arm", "rainbow", 40)
        time.sleep(3)
        
        # 6. 测试跑马灯效果
        rospy.loginfo("6. Testing marquee effect")
        self.send_command("chassis", "marquee", 70, [0, 0, 255])
        time.sleep(3)
        
        # 7. 测试所有区域
        rospy.loginfo("7. Testing all regions")
        self.send_command("all", "off")
        time.sleep(1)
        
        rospy.loginfo("=== Test Complete ===")
        
    def test_speed_range(self):
        """测试速度范围"""
        rospy.loginfo("=== Testing Speed Range ===")
        
        speeds = [0, 25, 50, 75, 100]
        for speed in speeds:
            rospy.loginfo(f"Testing speed: {speed}")
            self.send_command("chest", "breathing", speed, [255, 0, 0])
            time.sleep(2)
            
        self.send_command("all", "off")
        
    def test_custom_colors(self):
        """测试自定义颜色功能"""
        rospy.loginfo("=== Testing Custom Colors ===")
        
        # 1. 设置胸口渐变
        rospy.loginfo("1. Testing chest gradient")
        gradient = []
        for i in range(24):
            r = (i * 255 // 23)
            g = 255 - r
            gradient.extend([r, g, 0])
        self.send_command("chest", "custom", rgb_data=gradient)
        time.sleep(3)
        
        # 2. 设置左臂单色
        rospy.loginfo("2. Testing left arm single color")
        red_leds = [255, 0, 0] * 11  # 11个红色LED
        self.send_command("left_arm", "custom", rgb_data=red_leds)
        time.sleep(3)
        
        # 3. 设置底盘从中间开始的颜色
        rospy.loginfo("3. Testing chassis with start index")
        center_colors = [255, 255, 255] * 5  # 5个白色LED
        self.send_command("chassis", "custom", start_index=10, rgb_data=center_colors)
        time.sleep(3)
        
        self.send_command("all", "off")
        
    def test_effect_types(self):
        """测试所有效果类型"""
        rospy.loginfo("=== Testing All Effect Types ===")
        
        effects = [
            ("solid", [255, 0, 0]),
            ("breathing", [0, 255, 0]),
            ("flowing", [0, 0, 255]),
            ("marquee", [255, 255, 0]),
            ("rainbow", None)
        ]
        
        for effect, color in effects:
            rospy.loginfo(f"Testing effect: {effect}")
            self.send_command("chest", effect, 50, color)
            time.sleep(3)
            
        self.send_command("all", "off")
        
    def run_comprehensive_test(self):
        """运行综合测试"""
        rospy.loginfo("Starting comprehensive LED test...")
        
        self.test_all_commands()
        time.sleep(1)
        self.test_speed_range()
        time.sleep(1)
        self.test_custom_colors()
        time.sleep(1)
        self.test_effect_types()
        
        rospy.loginfo("Comprehensive test completed!")

if __name__ == '__main__':
    try:
        tester = LedTester()
        tester.run_comprehensive_test()
    except rospy.ROSInterruptException:
        pass
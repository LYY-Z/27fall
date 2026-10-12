#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist

import sys, select, termios, tty
import time

msg = ""


def getKey():
    tty.setraw(sys.stdin.fileno())
    rlist, _, _ = select.select([sys.stdin], [], [], 0.1)
    if rlist:
        key = sys.stdin.read(1)
    else:
        key = ''

    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
    return key


def vels(speed,turn):
    return "currently:\tspeed %s\tturn %s " % (speed,turn)

if __name__=="__main__":
    settings = termios.tcgetattr(sys.stdin)
    
    rclpy.init()
    node = Node('racecar_teleop')
    pub = node.create_publisher(Twist, '~/car/cmd_vel', 10)


    run = 0

    try:
        while(1):
            key = getKey()
            twist = Twist()
            if key == '1':
                twist.linear.x = 1500; twist.linear.y = 0; 
                twist.linear.z = 0
                twist.angular.x = 0; 
                twist.angular.y = 0; 
                twist.angular.z = 90
                print ("vel = 0")
            elif key == '2':
                twist.linear.x = 2500; twist.linear.y = 0; twist.linear.z = 0;
                twist.angular.x = 0; twist.angular.y = 0; twist.angular.z = 90;
                print ("vel = +Max")
            elif key == '3':
                twist.linear.x = 500; twist.linear.y = 0; twist.linear.z = 0;
                twist.angular.x = 0; twist.angular.y = 0; twist.angular.z = 90;
                print ("vel = -Max")
            else:
                twist.linear.x = 1500; twist.linear.y = 0; twist.linear.z = 0;
                twist.angular.x = 0; twist.angular.y = 0; twist.angular.z = 90;
                print ("stop")

            pub.publish(twist)
            
            

            if (key == '\x03'):   #for ctrl + c exit
                break

    except:
        print ("error")

    finally:
        twist = Twist()
        twist.linear.x = speed_mid; twist.linear.y = 0; twist.linear.z = 0
        twist.angular.x = 0; twist.angular.y = 0; twist.angular.z = turn_mid
        pub.publish(twist)

    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
    rclpy.shutdown()

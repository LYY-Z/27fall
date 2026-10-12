import rospy
import rosnode
import roslaunch
from tf_conversions import transformations
from math import pi
import tf
import csv
from geometry_msgs.msg import PoseStamped,Twist,PoseWithCovarianceStamped
import threading
from 项目源码.智能车自主导航系统.src.multi_goal.src.goal_loop import MultiGoals
import numpy as np
import os
import rospkg
# from mapBlur import mapBlur
import psutil
from visualization_msgs.msg import Marker
class Get_Point:
    def __init__(self, csv_write):
        rospy.init_node('get_point_node', anonymous=True)
        self.tf_listener = tf.TransformListener()
        self.csv_write = csv_write
        
        # 创建 Marker 发布者
        self.marker_pub = rospy.Publisher('/visualization_marker', Marker, queue_size=10)
        
        try:
            self.tf_listener.waitForTransform('map', 'base_footprint', rospy.Time(), rospy.Duration(1.0))
        except (tf.Exception, tf.ConnectivityException, tf.LookupException):
            rospy.loginfo("TF Initialization Error")

    def get_pos(self):
        try:
            (trans, rot) = self.tf_listener.lookupTransform('map', 'base_footprint', rospy.Time(0))
        except (tf.LookupException, tf.ConnectivityException, tf.ExtrapolationException):
            rospy.loginfo("tf Error")
            return None
        return trans[0], trans[1], rot[2], rot[3]

csv_dir = "/racecar_new/src/multi_goal/src/test.csv"

with open(csv_dir, 'w', encoding='utf8', newline='') as f:
    csv_write = csv.writer(f, delimiter=',', quoting=csv.QUOTE_MINIMAL)
    nav_point = Get_Point(csv_write)

    r = rospy.Rate(10)

    last_x = last_y = 0
    flg = 0  # 当前记录的点数

    while not rospy.is_shutdown():
        pos = nav_point.get_pos()
        if pos is None:
            continue  # 如果获取位置信息失败，跳过本次循环
            
        x, y, z, w = pos  # 解包位置信息

        # 判断是否需要记录
        if ((x - last_x)**2 + (y - last_y)**2)**0.5 >= 0.5 or flg == 0:
            csv_write.writerow([x, y, z, w])
            last_x = x
            last_y = y
            flg += 1  # 增加点的计数

            # 创建并发布 Marker
            marker = Marker()
            marker.header.frame_id = "map"
            marker.header.stamp = rospy.Time.now()
            marker.ns = "points"
            marker.id = flg  # 使用唯一 ID
            marker.type = Marker.SPHERE  # 选择球体形状
            marker.action = Marker.ADD

            # 设置位置和方向
            marker.pose.position.x = x
            marker.pose.position.y = y
            marker.pose.position.z = 0  # 根据需要设置 Z 坐标
            marker.pose.orientation.x = 0.0
            marker.pose.orientation.y = 0.0
            marker.pose.orientation.z = 0.0
            marker.pose.orientation.w = 1.0  # 使用有效的四元数

            # 设置缩放
            marker.scale.x = 0.2  # 球体的直径
            marker.scale.y = 0.2
            marker.scale.z = 0.2

            # 设置颜色
            marker.color.r = 1.0  # 红色
            marker.color.g = 0.0
            marker.color.b = 0.0
            marker.color.a = 1.0  # 不透明

            # 设置生存时间
            marker.lifetime = rospy.Duration(0)  # 永久可见
            marker.frame_locked = False

            # 发布 Marker
            nav_point.marker_pub.publish(marker)

        r.sleep()  # 控制循环频率
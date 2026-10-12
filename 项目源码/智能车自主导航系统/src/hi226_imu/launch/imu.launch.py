
# ROS2 Python launch file for hi226_imu
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
  return LaunchDescription([
    Node(
      package='hi226_imu',
      executable='hi226_imu_node',
      name='imu',
      output='screen',
      parameters=[{
        'port': '/dev/imu',
        'model': 'hi226',
        'baud': 115200
      }]
    )
  ])

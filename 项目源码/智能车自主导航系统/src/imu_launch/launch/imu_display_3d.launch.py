from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='serial_imu',
            executable='serial_imu',
            name='HI226',
            output='screen',
        ),
        Node(
            package='serial_imu',
            executable='display_3D_node.py',
            name='display_3D_node',
            output='screen',
        ),
    ])

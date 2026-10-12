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
            package='rviz2',
            executable='rviz2',
            name='rviz_hi226',
            output='screen',
        ),
    ])

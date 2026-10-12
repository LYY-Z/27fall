
# ROS2 Python launch file for rviz
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            'use_rviz', default_value='true', description='Whether to launch RViz'),
        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz',
            arguments=['-d', 'rviz/imu.rviz'],
            condition=lambda context: context.launch_configurations['use_rviz'] == 'true',
            output='screen'
        )
    ])

from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch.conditions import IfCondition
import os

def generate_launch_description():
    racecar_dir = os.path.join(os.path.dirname(__file__), '..')
    rviz_cfg = os.path.join(racecar_dir, 'rviz', 'amcl.rviz')
    return LaunchDescription([
        DeclareLaunchArgument('use_rviz', default_value='true'),
        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz',
            arguments=['-d', rviz_cfg],
            output='screen',
            condition=IfCondition(LaunchConfiguration('use_rviz')),
        ),
    ])

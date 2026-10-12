from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='joy',
            executable='joy_node',
            name='joy_node',
            output='screen',
            parameters=[{}],
        ),
        Node(
            package='racecar',
            executable='racecar_teleop.py',
            name='racecar_joy',
            output='screen',
            parameters=[{}],
        ),
    ])

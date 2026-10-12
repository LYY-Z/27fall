from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='encoder_driver',
            executable='encoder_driver_node1',
            name='wheel_odom',
            output='screen'
        )
    ])
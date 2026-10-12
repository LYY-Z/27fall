from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration

def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('inverted', default_value='false'),
        Node(
            package='ls01g',
            executable='ls01g',
            name='ls01g',
            output='screen',
            parameters=[{
                'scan_topic': 'scan',
                'laser_link': 'laser',
                'serial_port': '/dev/laser',
                'zero_as_max': False,
                'min_as_zero': False,
                'angle_disable_min': -1,
                'angle_disable_max': -1,
                'inverted': LaunchConfiguration('inverted'),
            }],
        ),
    ])

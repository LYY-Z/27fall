from launch import LaunchDescription
from launch_ros.actions import Node
import os

def generate_launch_description():
    pkg_share = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'ls01b', 'launch', 'includes'))
    filter_yaml = os.path.join(pkg_share, 'filter.yaml')
    return LaunchDescription([
        Node(
            package='ls01b_v2',
            executable='ls01b_v2',
            name='ls01b_v2',
            output='screen',
            parameters=[{
                'scan_topic': 'scan',
                'frame_id': 'laser_link',
                'serial_port': '/dev/laser',
                'baud_rate': 460800,
                'angle_resolution': 0.25,
                'zero_as_max': False,
                'min_as_zero': False,
                'rpm': 600,
                'angle_compensate': True,
            }, filter_yaml],
        ),
    ])

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
                'baud': 115200,
                'model': 'hi226'
            }]
        )
    ])
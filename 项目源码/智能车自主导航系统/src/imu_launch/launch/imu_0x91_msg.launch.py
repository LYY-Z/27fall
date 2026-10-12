from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='serial_imu',
            executable='serial_imu',
            name='imu_sonser_0x91',
            output='screen',
        ),
        # Node(
        #     package='serial_imu',
        #     executable='sub_0x91',
        #     name='sub_0x91',
        #     output='screen',
        # ),
    ])

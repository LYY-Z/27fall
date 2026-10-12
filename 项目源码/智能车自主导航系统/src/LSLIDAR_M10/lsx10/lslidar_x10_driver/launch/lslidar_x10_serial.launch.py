from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='lslidar_x10_driver',
            executable='lslidar_x10_driver_node',
            name='lslidar_x10_driver_node',
            output='screen',
            parameters=[{
                'lidar_name': 'M10',
                'serial_port': '/dev/laser',
                'interface_selection': 'serial',
                'child_frame_id': 'laser_link',
                'scan_topic': 'scan',
                'angle_disable_min': 0.0,
                'angle_disable_max': 0.0,
                'min_range': 0.3,
                'max_range': 100.0,
                'use_gps_ts': False,
            }],
        ),
        # 如需rviz2可取消注释
        # ExecuteProcess(
        #     cmd=['rviz2', '-d', '/path/to/lslidar_x10_driver/rviz/lslidar.rviz'],
        #     output='screen',
        # ),
    ])

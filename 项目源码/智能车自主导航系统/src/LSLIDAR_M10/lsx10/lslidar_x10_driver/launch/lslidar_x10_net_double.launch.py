from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import ExecuteProcess

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='lslidar_x10_driver',
            executable='lslidar_x10_driver_node',
            name='lslidar_x10_driver_node',
            namespace='LeftLidar',
            output='screen',
            parameters=[{
                'frame_id': 'laser_link',
                'device_ip': '192.168.1.200',
                'device_port': 2368,
                'difop_ip': '192.168.1.102',
                'difop_port': 2369,
                'lidar_name': 'M10',
                'interface_selection': 'net',
                'child_frame_id': 'laser_link',
                'scan_topic': 'scan',
                'angle_disable_min': 0.0,
                'angle_disable_max': 0.0,
                'min_range': 0,
                'max_range': 100.0,
                'use_gps_ts': False,
            }],
        ),
        Node(
            package='lslidar_x10_driver',
            executable='lslidar_x10_driver_node',
            name='lslidar_x10_driver_node',
            namespace='RightLidar',
            output='screen',
            parameters=[{
                'frame_id': 'laser_link',
                'device_ip': '192.168.1.200',
                'device_port': 2368,
                'difop_ip': '192.168.1.102',
                'difop_port': 2369,
                'lidar_name': 'M10',
                'interface_selection': 'net',
                'child_frame_id': 'laser_link',
                'scan_topic': 'scan',
                'angle_disable_min': 0.0,
                'angle_disable_max': 0.0,
                'min_range': 0,
                'max_range': 100.0,
                'use_gps_ts': False,
            }],
        ),
        ExecuteProcess(
            cmd=['rviz2', '-d', '/path/to/lslidar_x10_decoder/rviz/default.rviz'],
            output='screen',
        ),
    ])

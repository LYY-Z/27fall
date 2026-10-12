from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import ExecuteProcess

def generate_launch_description():
    return LaunchDescription([
        ExecuteProcess(
            cmd=['ros2', 'run', 'tf2_ros', 'static_transform_publisher', '0.0', '0.0', '0.15', '0.0', '0.0', '0.0', '/base_footprint', '/base_link', '1'],
            output='screen',
        ),
        ExecuteProcess(
            cmd=['ros2', 'run', 'tf2_ros', 'static_transform_publisher', '0.07', '0.0', '0.0', '0.0', '0.0', '0.0', '/base_link', '/laser_link', '1'],
            output='screen',
        ),
        ExecuteProcess(
            cmd=['ros2', 'run', 'tf2_ros', 'static_transform_publisher', '0.1653', '0.0', '0.0', '0.0', '0.0', '0.0', '/base_link', '/IMU_link', '1'],
            output='screen',
        ),
    ])

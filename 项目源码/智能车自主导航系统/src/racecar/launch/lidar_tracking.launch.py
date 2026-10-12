from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration

def generate_launch_description():
    return LaunchDescription([
        # 如需参数可通过arg传递，示例：
        # DeclareLaunchArgument('speed', default_value='1550'),
        Node(
            package='lidar_tracking',
            executable='lidar_tracking_nnew',
            name='lidar_tracking_nnew',
            output='screen',
            parameters=[{
                'topic': 'car/cmd_vel',
                'speed': 1550,
                'kp': 2.2,
                'ki': 0,
                'kd': 0.66,
                'max_left_dis': 1.5,
                'max_right_dis': 1.8,
                'rate1': 1.0,
                'rate2': 2.2,
                'rate3': 0.5,
                'middle_angle': 85,
                'vaild_bucket_threshold': 2,
                'bucket_threshold': 5,
                'speed_time': 3.0,
            }],
        ),
    ])

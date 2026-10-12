from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='rf2o_laser_odometry',
            executable='rf2o_laser_odometry_node',
            name='rf2o_laser_odometry',
            parameters=[{
                'laser_scan_topic': '/scan',
                'base_frame_id': 'base_footprint',
                'odom_topic': 'odom',
                'publish_tf': False,
                'odom_frame_id': 'odom',
                'freq': 9.0,
                'verbose': True,
                'init_pose_from_topic': '',
            }],
        ),
    ])

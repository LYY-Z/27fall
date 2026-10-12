from launch import LaunchDescription
from launch_ros.actions import Node
from launch.substitutions import LaunchConfiguration
from launch.actions import DeclareLaunchArgument, ExecuteProcess

def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('tf_map_scanmatch_transform_frame_name', default_value='scanmatcher_frame'),
        DeclareLaunchArgument('base_frame', default_value='base_footprint'),
        DeclareLaunchArgument('odom_frame', default_value='nav'),
        DeclareLaunchArgument('pub_map_odom_transform', default_value='true'),
        DeclareLaunchArgument('scan_subscriber_queue_size', default_value='5'),
        DeclareLaunchArgument('scan_topic', default_value='scan'),
        DeclareLaunchArgument('map_size', default_value='2048'),
        Node(
            package='hector_mapping',
            executable='hector_mapping',
            name='hector_mapping',
            output='screen',
            parameters=[{
                'map_frame': 'map',
                'base_frame': LaunchConfiguration('base_frame'),
                'odom_frame': LaunchConfiguration('odom_frame'),
                'use_tf_scan_transformation': True,
                'use_tf_pose_start_estimate': False,
                'pub_map_odom_transform': LaunchConfiguration('pub_map_odom_transform'),
                'map_resolution': 0.050,
                'map_size': LaunchConfiguration('map_size'),
                'map_start_x': 0.5,
                'map_start_y': 0.5,
                'map_multi_res_levels': 2,
                'update_factor_free': 0.4,
                'update_factor_occupied': 0.9,
                'map_update_distance_thresh': 0.4,
                'map_update_angle_thresh': 0.06,
                'laser_z_min_value': -1.0,
                'laser_z_max_value': 1.0,
                'advertise_map_service': True,
                'scan_subscriber_queue_size': LaunchConfiguration('scan_subscriber_queue_size'),
                'scan_topic': LaunchConfiguration('scan_topic'),
                'tf_map_scanmatch_transform_frame_name': LaunchConfiguration('tf_map_scanmatch_transform_frame_name'),
            }],
        ),
        ExecuteProcess(
            cmd=['ros2', 'run', 'tf2_ros', 'static_transform_publisher', '0', '0', '0', '0', '0', '0', 'map', 'nav', '100'],
            output='screen',
        ),
    ])

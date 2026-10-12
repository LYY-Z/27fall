from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
import os

def generate_launch_description():
    # 路径请根据实际情况调整
    racecar_dir = os.path.join(os.path.dirname(__file__), '..')
    includes_dir = os.path.join(racecar_dir, 'launch', 'includes')
    param_dir = os.path.join(racecar_dir, 'param')
    encoder_driver_dir = os.path.abspath(os.path.join(racecar_dir, '..', 'encoder_driver'))

    return LaunchDescription([
        DeclareLaunchArgument('use_rviz', default_value='false'),
        # ODOMETRY
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(os.path.join(includes_dir, 'rf2o.launch.py')),
        ),
        # wheel odometry
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(os.path.join(encoder_driver_dir, 'launch', 'wheel_odom.launch.py')),
        ),
        # nav2 map_server
        Node(
            package='nav2_map_server',
            executable='map_server',
            name='map_server',
            output='screen',
            parameters=[os.path.join(param_dir, 'map_server_params.yaml')],
        ),
        # nav2 amcl
        Node(
            package='nav2_amcl',
            executable='amcl',
            name='amcl',
            output='screen',
            parameters=[os.path.join(param_dir, 'amcl_params.yaml')],
        ),
        # nav2 planner_server
        Node(
            package='nav2_planner',
            executable='planner_server',
            name='planner_server',
            output='screen',
            parameters=[os.path.join(param_dir, 'planner_server_params.yaml')],
        ),
        # nav2 controller_server
        Node(
            package='nav2_controller',
            executable='controller_server',
            name='controller_server',
            output='screen',
            parameters=[os.path.join(param_dir, 'controller_server_params.yaml')],
        ),
        # nav2 bt_navigator
        Node(
            package='nav2_bt_navigator',
            executable='bt_navigator',
            name='bt_navigator',
            output='screen',
            parameters=[os.path.join(param_dir, 'bt_navigator_params.yaml')],
        ),
        # nav2 waypoint_follower
        Node(
            package='nav2_waypoint_follower',
            executable='waypoint_follower',
            name='waypoint_follower',
            output='screen',
            parameters=[os.path.join(param_dir, 'waypoint_follower_params.yaml')],
        ),
        # nav2 lifecycle_manager
        Node(
            package='nav2_lifecycle_manager',
            executable='lifecycle_manager',
            name='lifecycle_manager_navigation',
            output='screen',
            parameters=[{'autostart': True, 'node_names': [
                'map_server', 'amcl', 'planner_server', 'controller_server', 'bt_navigator', 'waypoint_follower'
            ]}],
        ),
        Node(
            package='racecar',
            executable='car_controller_new',
            name='car_controller',
            output='screen',
            parameters=[{
                'Vcmd': 1.0,
                'baseSpeed': 40,
                'baseAngle': 90.0,
                'Angle_gain_p': -5.5,
                'Angle_gain_d': -3.0,
                'Lfw': 1.1,
                'vp_max_base': 55,
                'vp_min': 45,
                'all': False,
            }],
        ),
        # 如需rviz2可取消注释
        # ExecuteProcess(
        #     cmd=['rviz2', '-d', os.path.join(racecar_dir, 'rviz', 'amcl.rviz')],
        #     condition=IfCondition(LaunchConfiguration('use_rviz')),
        #     output='screen',
        # ),
    ])

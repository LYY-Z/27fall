from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
import os

def generate_launch_description():
    racecar_dir = os.path.join(os.path.dirname(__file__), '..')
    includes_dir = os.path.join(racecar_dir, 'launch', 'includes')
    param_dir = os.path.join(racecar_dir, 'param')
    encoder_driver_dir = os.path.abspath(os.path.join(racecar_dir, '..', 'encoder_driver'))
    return LaunchDescription([
        # ODOMETRY
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(os.path.join(includes_dir, 'rf2o.launch.py')),
        ),
        # wheel odometry
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(os.path.join(encoder_driver_dir, 'launch', 'wheel_odom.launch.py')),
        ),
        # Robot_Localization
        Node(
            package='robot_localization',
            executable='ekf_localization_node',
            name='ekf_se',
            output='screen',
            parameters=[os.path.join(param_dir, 'ekf_params.yaml')],
        ),
    ])

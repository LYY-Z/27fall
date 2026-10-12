from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
import os

def generate_launch_description():
    racecar_dir = os.path.join(os.path.dirname(__file__), '..')
    includes_dir = os.path.join(racecar_dir, 'launch', 'includes')
    return LaunchDescription([
        # TF setting
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(os.path.join(includes_dir, 'car_tf.launch.py')),
        ),
        # Car
        Node(
            package='racecar_driver',
            executable='racecar_driver_node',
            name='racecar_driver_node',
            output='screen',
            parameters=[{}],
        ),
    ])

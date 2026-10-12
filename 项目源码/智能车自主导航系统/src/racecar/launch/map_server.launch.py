from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
import os

def generate_launch_description():
    racecar_dir = os.path.join(os.path.dirname(__file__), '..')
    includes_dir = os.path.join(racecar_dir, 'launch', 'includes')
    map_yaml = os.path.join(racecar_dir, 'map', 'map1.yaml')
    return LaunchDescription([
        Node(
            package='nav2_map_server',
            executable='map_server',
            name='map_server',
            output='screen',
            parameters=[{'yaml_filename': map_yaml}],
        ),
        # 如需lidar_loc节点可取消注释
        # Node(
        #     package='czj_pkg',
        #     executable='lidar_loc',
        #     name='lidar_loc',
        #     output='screen',
        #     parameters=[{'base_frame': 'base_footprint', 'laser_frame': 'laser_link'}],
        # ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(os.path.join(includes_dir, 'amcl.launch.py')),
        ),
    ])

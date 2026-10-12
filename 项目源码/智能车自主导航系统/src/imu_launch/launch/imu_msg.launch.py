from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
import os
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    imu_package = LaunchConfiguration('imu_package', default='spec')
    launch_dir = os.path.join(get_package_share_directory('imu_launch'), 'launch')
    return LaunchDescription([
        DeclareLaunchArgument(
            'imu_package',
            default_value='spec',
            description='package type [spec,0x91]'
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(launch_dir, f"imu_{imu_package.perform({})}_msg.launch.py")
            ),
        ),
    ])

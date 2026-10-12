from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
import os

def generate_launch_description():
    racecar_dir = os.path.join(os.path.dirname(__file__), '..')
    includes_dir = os.path.join(racecar_dir, 'launch', 'includes')
    lslidar_dir = os.path.abspath(os.path.join(racecar_dir, '..', 'LSLIDAR_M10', 'lsx10', 'lslidar_x10_driver', 'launch'))
    imu_launch_dir = os.path.abspath(os.path.join(racecar_dir, '..', 'imu_launch', 'launch'))
    encoder_driver_dir = os.path.abspath(os.path.join(racecar_dir, '..', 'encoder_driver'))
    return LaunchDescription([
        # TF setting
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(os.path.join(includes_dir, 'car_tf.launch.py')),
        ),
        # lslidar_x10_serial
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(os.path.join(lslidar_dir, 'lslidar_x10_serial.launch.py')),
        ),
        # imu_package arg
        DeclareLaunchArgument('imu_package', default_value='spec', description='package type [spec,0x91]'),
        # imu_launch
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(os.path.join(imu_launch_dir, 'imu_' + LaunchConfiguration('imu_package') + '_msg.launch.py')),
        ),
        # encoder_driver
        Node(
            package='encoder_driver',
            executable='Encoder_vel.py',
            name='encoder_vel',
            output='screen',
            parameters=[{
                'serial_port': '/dev/encoder',
                'k': 0.7,
                'baud_rate': 57600,
            }],
        ),
        # Car
        Node(
            package='racecar_driver',
            executable='racecar_driver_node',
            name='racecar_driver_node',
            output='screen',
            parameters=[{}],
        ),
        # rosbridge_server
        Node(
            package='rosbridge_server',
            executable='rosbridge_websocket',
            name='rosbridge_server',
            output='screen',
            parameters=[{'websocket_port': 9090}],
        ),
        # 如需rf2o_Laser_Odometry、wheel_odom、robot_localization可取消注释
        # IncludeLaunchDescription(
        #     PythonLaunchDescriptionSource(os.path.join(includes_dir, 'rf2o.launch.py')),
        # ),
        # IncludeLaunchDescription(
        #     PythonLaunchDescriptionSource(os.path.join(encoder_driver_dir, 'launch', 'wheel_odom.launch.py')),
        # ),
        # Node(
        #     package='robot_localization',
        #     executable='ekf_localization_node',
        #     name='ekf_se',
        #     output='screen',
        #     parameters=[os.path.join(racecar_dir, 'param', 'ekf_params.yaml')],
        # ),
    ])

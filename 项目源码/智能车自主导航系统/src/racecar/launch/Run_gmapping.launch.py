from launch import LaunchDescription
from launch_ros.actions import Node

# ROS2下gmapping推荐使用slam_gmapping包（如slam_gmapping_ros2），参数格式需适配yaml

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='slam_gmapping',  # ROS2下推荐slam_gmapping_ros2或移植包
            executable='slam_gmapping',
            name='slam_gmapping',
            output='screen',
            parameters=[{
                'map_update_interval': 0.01,
                'maxUrange': 10,
                'maxRange': 10,
                'sigma': 0.05,
                'kernelSize': 3,
                'lstep': 0.05,
                'astep': 0.05,
                'iterations': 5,
                'lsigma': 0.075,
                'ogain': 3.0,
                'lskip': 0,
                'minimumScore': 30,
                'srr': 0.01,
                'srt': 0.02,
                'str': 0.01,
                'stt': 0.02,
                'linearUpdate': 0.05,
                'angularUpdate': 0.0436,
                'temporalUpdate': -1.0,
                'resampleThreshold': 0.5,
                'particles': 1,
                'xmin': -1.0,
                'ymin': -1.0,
                'xmax': 1.0,
                'ymax': 1.0,
                'delta': 0.05,
                'llsamplerange': 0.01,
                'llsamplestep': 0.01,
                'lasamplerange': 0.005,
                'lasamplestep': 0.005,
                'odom_frame': 'odom',
                'base_frame': 'base_footprint',
            }],
            remappings=[('scan', 'scan')],
        ),
        # 如需hector_mapping、move_base、car_controller等节点，可参考注释内容补充
    ])

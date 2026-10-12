from setuptools import setup

package_name = 'encoder_driver'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='your_name',
    maintainer_email='your_email@todo.todo',
    description='ROS2 encoder driver package',
    license='TODO',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'encoder_vel = encoder_driver.Encoder_vel_ros2:main',
        ],
    },
)

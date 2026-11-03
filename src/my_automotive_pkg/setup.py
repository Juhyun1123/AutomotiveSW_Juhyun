from setuptools import find_packages, setup
from glob import glob
import os

package_name = 'my_automotive_pkg'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        (
            'share/ament_index/resource_index/packages',
            ['resource/' + package_name]
        ),
        (
            'share/' + package_name,
            ['package.xml']
        ),

        # Launch
        (
            os.path.join('share', package_name, 'launch'),
            glob('launch/*.launch.py')
        ),

        # Config
        (
            os.path.join('share', package_name, 'config'),
            glob('config/*.yaml') + glob('config/*.rviz')
        ),

        # URDF / Xacro
        (
            os.path.join('share', package_name, 'urdf'),
            glob('urdf/*')
        ),
        (os.path.join('share', package_name, 'worlds'), glob('worlds/*.sdf')),
    ],
    package_data={'': ['py.typed']},
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Juhyun',
    maintainer_email='gjhy1123@gmail.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'sensor_listener = my_automotive_pkg.sensor_listener:main',
            'static_tf = my_automotive_pkg.static_tf_broadcaster:main',
            'dynamic_tf = my_automotive_pkg.dynamic_tf_broadcaster:main',
            'tf_listener = my_automotive_pkg.tf_listener:main',
            'keyboard_teleop = my_automotive_pkg.keyboard_teleop:main',
            'ackermann_controller = my_automotive_pkg.ackermann_controller:main',
            'custom_marker_publisher = my_automotive_pkg.custom_marker_publisher:main',
            #'emergency_stop = my_automotive_pkg.emergency_stop_node:main',
            'emergency_stop = answer.emergency_stop_node:main',
            'emergency_stop_node = answer.emergency_stop_node:main',
        ],
    },
)

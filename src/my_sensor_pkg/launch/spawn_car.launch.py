"""Launch the copied vehicle, sensors and track in Gazebo Sim."""
import os
import xacro
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    share = get_package_share_directory('my_sensor_pkg')
    description = xacro.process_file(os.path.join(share, 'urdf', 'vehicle.urdf.xacro')).toxml()
    return LaunchDescription([
        DeclareLaunchArgument('sensor_listener', default_value='true'),
        ExecuteProcess(cmd=['gz', 'sim', '-r', os.path.join(share, 'worlds', 'car_track.sdf')], output='screen'),
        Node(package='robot_state_publisher', executable='robot_state_publisher',
             parameters=[{'robot_description': description, 'use_sim_time': True}], output='screen'),
        Node(package='ros_gz_sim', executable='create',
             arguments=['-world', 'car_track_world', '-name', 'auto_vehicle',
                        '-topic', '/robot_description', '-x', '0', '-y', '-4', '-z', '0.15'], output='screen'),
        Node(package='ros_gz_bridge', executable='parameter_bridge',
             parameters=[{'config_file': os.path.join(share, 'config', 'vehicle_sensor_bridge.yaml')}], output='screen'),
        Node(package='my_sensor_pkg', executable='sensor_listener',
             parameters=[{'use_sim_time': True}], condition=IfCondition(LaunchConfiguration('sensor_listener')),
             output='screen'),
    ])

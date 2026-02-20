import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    config = os.path.join(
        get_package_share_directory('ntrip_client'),
        'config',
        'ntrip_params.yaml'
    )

    return LaunchDescription([
        Node(
            package='ntrip_client',
            executable='ntrip_client_node',
            name='ntrip_client_node',
            parameters=[config],
            output='screen',
        ),
    ])

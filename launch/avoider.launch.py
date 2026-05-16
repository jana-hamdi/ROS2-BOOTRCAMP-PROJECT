"""
avoider.launch.py
=================
Launches the obstacle_avoider node with configurable parameters.

Usage:
    ros2 launch obstacle_avoider avoider.launch.py
    ros2 launch obstacle_avoider avoider.launch.py front_threshold:=0.4 forward_speed:=0.2
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():

    # ------------------------------------------------------------------
    # Declare overridable launch arguments
    # ------------------------------------------------------------------
    front_threshold_arg = DeclareLaunchArgument(
        'front_threshold',
        default_value='0.55',
        description='Distance (m) below which the front is considered blocked'
    )

    forward_speed_arg = DeclareLaunchArgument(
        'forward_speed',
        default_value='0.18',
        description='Linear velocity (m/s) when path is clear'
    )

    turn_speed_arg = DeclareLaunchArgument(
        'turn_speed',
        default_value='0.60',
        description='Angular velocity (rad/s) when avoiding an obstacle'
    )

    # ------------------------------------------------------------------
    # Node definition
    # ------------------------------------------------------------------
    avoider_node = Node(
        package='obstacle_avoider',
        executable='avoider',
        name='obstacle_avoider',
        output='screen',
        emulate_tty=True,          # keeps coloured log output in the terminal
        parameters=[{
            'front_threshold': LaunchConfiguration('front_threshold'),
            'forward_speed':   LaunchConfiguration('forward_speed'),
            'turn_speed':      LaunchConfiguration('turn_speed'),
        }]
    )

    return LaunchDescription([
        front_threshold_arg,
        forward_speed_arg,
        turn_speed_arg,
        avoider_node,
    ])

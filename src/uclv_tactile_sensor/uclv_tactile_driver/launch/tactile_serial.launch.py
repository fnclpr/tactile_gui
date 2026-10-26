from launch import LaunchDescription
from launch.substitutions import LaunchConfiguration
from launch.actions import DeclareLaunchArgument
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        # Declaration of argument
        DeclareLaunchArgument('serial_port', default_value='/dev/ttyUSB0', description='Serial port'),
        DeclareLaunchArgument('baud_rate', default_value='1000000', description='Baud rate'),
        DeclareLaunchArgument('serial_timeout', default_value='1000', description='Serial timeout'),
        DeclareLaunchArgument('rows', default_value='5', description='Number of rows'),
        DeclareLaunchArgument('cols', default_value='5', description='Number of columns'),
        DeclareLaunchArgument('tf_prefix', default_value='', description='TF prefix'),
        DeclareLaunchArgument('frame_id', default_value='fingertip0', description='Frame ID'),
        DeclareLaunchArgument('output_topic', default_value='tactile_voltage/raw', description='Output topic'),

        # Read from serial node
        Node(
            package='uclv_tactile_driver',
            executable='read_tactile_serial',
            name='read_tactile_serial',
            output='screen',
            parameters=[{
                'serial_port': LaunchConfiguration('serial_port'),
                'baud_rate': LaunchConfiguration('baud_rate'),
                'serial_timeout': LaunchConfiguration('serial_timeout'),
                'rows': LaunchConfiguration('rows'),
                'cols': LaunchConfiguration('cols'),
                'tf_prefix': LaunchConfiguration('tf_prefix'),
                'frame_id': LaunchConfiguration('frame_id'),
                'output_topic': LaunchConfiguration('output_topic'),
            }]
        ),
    ])

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch_ros.actions import Node
from launch.substitutions import LaunchConfiguration, PythonExpression

def generate_launch_description():
    return LaunchDescription([
        # Declaration of argument
        DeclareLaunchArgument('serial_port', default_value='/dev/ttyUSB0', description='Serial port'),
        DeclareLaunchArgument('baud_rate', default_value='1000000', description='Baud rate'),
        DeclareLaunchArgument('serial_timeout', default_value='1000', description='Serial timeout'),
        DeclareLaunchArgument('rows', default_value='5', description='Number of rows'),
        DeclareLaunchArgument('cols', default_value='5', description='Number of columns'),
        DeclareLaunchArgument('default_num_samples', default_value='100', description='Default number of samples'),
        DeclareLaunchArgument('tf_prefix', default_value='', description='TF prefix'),
        DeclareLaunchArgument('frame_id', default_value='fingertip0', description='Frame ID'),
        DeclareLaunchArgument('output_topic', default_value='tactile_voltage/raw', description='Output topic'),

        # Invariant args
        # DeclareLaunchArgument('voltage_raw_topic', default_value='tactile_voltage/raw', description='Raw voltage topic'),
        # DeclareLaunchArgument('voltage_raw_checked_topic', default_value=PythonExpression(['"', LaunchConfiguration('voltage_raw_topic'), '_checked"']), description='Checked raw voltage topic'),
        DeclareLaunchArgument('voltage_rect_topic', default_value='tactile_voltage/rect', description='Rectified voltage topic'),
        DeclareLaunchArgument('action_compute_bias', default_value='compute_bias_action', description='Compute bias action topic'),

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

        # Remove bias node
        Node(
            package='uclv_tactile_driver',
            executable='remove_bias',
            name='remove_bias',
            output='screen',
            parameters=[{
                'out_voltage_topic': LaunchConfiguration('voltage_rect_topic'),
                'action_compute_bias': LaunchConfiguration('action_compute_bias'),
                'default_num_samples': LaunchConfiguration('default_num_samples'),
                'num_voltages': PythonExpression([LaunchConfiguration('cols'), ' * ', LaunchConfiguration('rows')]),
            }],
        ),

    ])

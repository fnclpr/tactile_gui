from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch_ros.actions import Node
from launch.substitutions import LaunchConfiguration, PythonExpression

def generate_launch_description():
    return LaunchDescription([
        # Dichiarazione Argomenti
        DeclareLaunchArgument('serial_port', default_value='/dev/ttyUSB0', description='Porta seriale'),
        DeclareLaunchArgument('baud_rate', default_value='1000000', description='Baud rate'),
        DeclareLaunchArgument('serial_timeout', default_value='1000', description='Timeout seriale (ms)'),
        DeclareLaunchArgument('rows', default_value='5', description='Numero righe'),
        DeclareLaunchArgument('cols', default_value='5', description='Numero colonne'),
        DeclareLaunchArgument('default_num_samples', default_value='100', description='Campioni per la tara'),
        DeclareLaunchArgument('tf_prefix', default_value='', description='TF prefix'),
        DeclareLaunchArgument('frame_id', default_value='fingertip0', description='Frame ID'),
        DeclareLaunchArgument('output_topic', default_value='tactile_voltage/raw', description='Topic raw'),
        DeclareLaunchArgument('voltage_rect_topic', default_value='tactile_voltage/rect', description='Topic debiased'),
        DeclareLaunchArgument('action_compute_bias', default_value='compute_bias_action', description='Nome Action Server'),

        # 1. Nodo Lettura Seriale (C++)
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

        # 2. Nodo Filtro Bias (C++)
        Node(
            package='uclv_tactile_driver',
            executable='remove_bias',
            name='remove_bias',
            output='screen',
            parameters=[{
                'in_voltage_topic': LaunchConfiguration('output_topic'),
                'out_voltage_topic': LaunchConfiguration('voltage_rect_topic'),
                'action_compute_bias': LaunchConfiguration('action_compute_bias'),
                'default_num_samples': LaunchConfiguration('default_num_samples'),
                'num_voltages': PythonExpression([LaunchConfiguration('cols'), ' * ', LaunchConfiguration('rows')]),
            }],
        ),

        # 3. Interfaccia Grafica Heatmap (Python)
        Node(
            package='tactile_gui',
            executable='heatmap_gui',
            name='tactile_heatmap_gui',
            output='screen',
            parameters=[{
                'raw_topic': LaunchConfiguration('output_topic'),
                'debiased_topic': LaunchConfiguration('voltage_rect_topic'),
                'action_name': LaunchConfiguration('action_compute_bias'),
                'rows': LaunchConfiguration('rows'),
                'cols': LaunchConfiguration('cols'),
            }]
        ),
    ])
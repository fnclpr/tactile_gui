from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration

def generate_launch_description():
    # Definisce un argomento per il topic, utile per passare da raw a rect
    topic_name_arg = DeclareLaunchArgument(
        'topic_name',
        default_value='tactile_voltage/rect',
        description='Il topic della matrice voltaggio da visualizzare'
    )

    gui_node = Node(
        package='tactile_gui',
        executable='heatmap_gui',
        name='heatmap_gui',
        output='screen',
        parameters=[{
            'topic_name': LaunchConfiguration('topic_name'),
            'rows': 5,
            'cols': 5
        }]
    )

    return LaunchDescription([
        topic_name_arg,
        gui_node
    ])
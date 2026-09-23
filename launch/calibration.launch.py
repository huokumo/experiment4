from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, SetEnvironmentVariable
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    package_dir = Path(get_package_share_directory("experiment4"))
    gazebo_launch = Path(get_package_share_directory("gazebo_ros")) / "launch" / "gazebo.launch.py"
    world = package_dir / "worlds" / "calibration_room.world"
    robot_xacro = package_dir / "urdf" / "differential_robot.urdf.xacro"
    rviz_config = package_dir / "config" / "experiment4.rviz"

    config_file = LaunchConfiguration("config_file")
    start_rviz = LaunchConfiguration("rviz")
    robot_description = ParameterValue(Command(["xacro ", str(robot_xacro)]), value_type=str)

    common_parameters = [config_file, {"use_sim_time": True}]

    return LaunchDescription([
        SetEnvironmentVariable("GAZEBO_MASTER_URI", "http://127.0.0.1:11346"),
        DeclareLaunchArgument(
            "config_file",
            default_value=str(package_dir / "config" / "sensor_calibration.yaml"),
        ),
        DeclareLaunchArgument("rviz", default_value="true"),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(str(gazebo_launch)),
            launch_arguments={"world": str(world), "verbose": "false"}.items(),
        ),
        Node(
            package="robot_state_publisher",
            executable="robot_state_publisher",
            name="robot_state_publisher",
            parameters=[{"robot_description": robot_description, "use_sim_time": True}],
            output="screen",
        ),
        Node(
            package="gazebo_ros",
            executable="spawn_entity.py",
            name="spawn_diffbot",
            arguments=["-topic", "robot_description", "-entity", "exp4_diffbot", "-x", "0", "-y", "0", "-z", "0.15"],
            output="screen",
        ),
        Node(package="experiment4", executable="lidar_cloud_relay", name="lidar_cloud_relay", parameters=common_parameters),
        Node(package="experiment4", executable="imu_fault_injector", name="imu_fault_injector", parameters=common_parameters),
        Node(package="experiment4", executable="imu_bias_corrector", name="imu_bias_corrector", parameters=common_parameters),
        Node(package="experiment4", executable="camera_interface_adapter", name="camera_interface_adapter", parameters=common_parameters),
        Node(
            package="rviz2",
            executable="rviz2",
            name="experiment4_rviz",
            arguments=["-d", str(rviz_config)],
            parameters=[{"use_sim_time": True}],
            condition=IfCondition(start_rviz),
            output="screen",
        ),
    ])

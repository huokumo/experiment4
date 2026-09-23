from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    package_dir = Path(get_package_share_directory("experiment4"))
    return LaunchDescription([
        DeclareLaunchArgument("rviz", default_value="true"),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(str(package_dir / "launch" / "calibration.launch.py")),
            launch_arguments={
                "config_file": str(package_dir / "config" / "sensor_calibration_fault.yaml"),
                "rviz": LaunchConfiguration("rviz"),
            }.items(),
        )
    ])

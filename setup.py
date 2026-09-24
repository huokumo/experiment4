from glob import glob
from setuptools import find_packages, setup


package_name = "experiment4"

setup(
    name=package_name,
    version="1.0.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        ("share/" + package_name + "/config", glob("config/*")),
        ("share/" + package_name + "/launch", glob("launch/*.launch.py")),
        ("share/" + package_name + "/scripts", glob("scripts/*.py")),
        ("share/" + package_name + "/urdf", glob("urdf/*")),
        ("share/" + package_name + "/worlds", glob("worlds/*")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="Course Team",
    maintainer_email="course@example.com",
    description="Sensor calibration and interface adaptation lab for ROS 2 Humble.",
    license="Apache-2.0",
    entry_points={
        "console_scripts": [
            "calculate_imu_bias = experiment4.entrypoints:calculate_imu_bias",
            "camera_interface_adapter = experiment4.entrypoints:camera_interface_adapter",
            "collect_imu_samples = experiment4.entrypoints:collect_imu_samples",
            "diagnose_calibration = experiment4.entrypoints:diagnose_calibration",
            "evaluate_lidar_extrinsic = experiment4.entrypoints:evaluate_lidar_extrinsic",
            "imu_bias_corrector = experiment4.entrypoints:imu_bias_corrector",
            "imu_fault_injector = experiment4.entrypoints:imu_fault_injector",
            "lidar_cloud_relay = experiment4.entrypoints:lidar_cloud_relay",
            "verify_calibration = experiment4.entrypoints:verify_calibration",
        ],
    },
)

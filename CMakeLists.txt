cmake_minimum_required(VERSION 3.8)
project(experiment4)

find_package(ament_cmake REQUIRED)

install(
  DIRECTORY
    config
    launch
    urdf
    worlds
  DESTINATION share/${PROJECT_NAME}
)

install(
  PROGRAMS
    scripts/calculate_imu_bias.py
    scripts/camera_interface_adapter.py
    scripts/collect_imu_samples.py
    scripts/evaluate_lidar_extrinsic.py
    scripts/imu_bias_corrector.py
    scripts/imu_fault_injector.py
    scripts/lidar_cloud_relay.py
    scripts/verify_calibration.py
  DESTINATION lib/${PROJECT_NAME}
)

ament_package()

from pathlib import Path
from runpy import run_path

from ament_index_python.packages import get_package_share_directory


def run_script(name):
    script = Path(get_package_share_directory("experiment4")) / "scripts" / f"{name}.py"
    return run_path(str(script), run_name="experiment4_console_script")["main"]()


def calculate_imu_bias():
    return run_script("calculate_imu_bias")


def camera_interface_adapter():
    return run_script("camera_interface_adapter")


def collect_imu_samples():
    return run_script("collect_imu_samples")


def evaluate_lidar_extrinsic():
    return run_script("evaluate_lidar_extrinsic")


def imu_bias_corrector():
    return run_script("imu_bias_corrector")


def imu_fault_injector():
    return run_script("imu_fault_injector")


def lidar_cloud_relay():
    return run_script("lidar_cloud_relay")


def verify_calibration():
    return run_script("verify_calibration")

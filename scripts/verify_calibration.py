#!/usr/bin/env python3

import math
import statistics
import sys
import time

import rclpy
from rclpy.duration import Duration
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from rclpy.time import Time
from sensor_msgs.msg import CameraInfo, Image, Imu, PointCloud2
from tf2_ros import Buffer, TransformException, TransformListener


class CalibrationVerifier(Node):
    def __init__(self):
        super().__init__("verify_calibration")
        self.raw_lidar = None
        self.calibrated_lidar = None
        self.raw_imu = None
        self.corrected_imu = []
        self.camera_image = None
        self.camera_info = None
        self.subscriptions = [
            self.create_subscription(PointCloud2, "/mid360/points", self.set_raw_lidar, qos_profile_sensor_data),
            self.create_subscription(PointCloud2, "/perception/lidar/points", self.set_calibrated_lidar, qos_profile_sensor_data),
            self.create_subscription(Imu, "/vendor/imu/data_raw", self.set_raw_imu, qos_profile_sensor_data),
            self.create_subscription(Imu, "/perception/imu/data", self.add_corrected_imu, qos_profile_sensor_data),
            self.create_subscription(Image, "/perception/camera/image_raw", self.set_camera_image, qos_profile_sensor_data),
            self.create_subscription(CameraInfo, "/perception/camera/camera_info", self.set_camera_info, qos_profile_sensor_data),
        ]
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

    def set_raw_lidar(self, message):
        self.raw_lidar = message

    def set_calibrated_lidar(self, message):
        self.calibrated_lidar = message

    def set_raw_imu(self, message):
        self.raw_imu = message

    def add_corrected_imu(self, message):
        if len(self.corrected_imu) < 200:
            self.corrected_imu.append(message)

    def set_camera_image(self, message):
        self.camera_image = message

    def set_camera_info(self, message):
        self.camera_info = message

    def collect(self, timeout_seconds=20.0):
        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            rclpy.spin_once(self, timeout_sec=0.1)
            complete = all([
                self.raw_lidar is not None,
                self.calibrated_lidar is not None,
                self.raw_imu is not None,
                len(self.corrected_imu) >= 100,
                self.camera_image is not None,
                self.camera_info is not None,
            ])
            if complete:
                return

    def calibrated_transform(self):
        try:
            return self.tf_buffer.lookup_transform(
                "base_link",
                "mid360_calibrated",
                Time(),
                timeout=Duration(seconds=1.0),
            )
        except TransformException:
            return None


def report(passed, message):
    print(f"[{'PASS' if passed else 'FAIL'}] {message}")
    return int(passed)


def rotation_angle(rotation):
    norm = math.sqrt(rotation.x ** 2 + rotation.y ** 2 + rotation.z ** 2 + rotation.w ** 2)
    if norm == 0.0:
        return math.inf
    w = max(-1.0, min(1.0, rotation.w / norm))
    return 2.0 * math.acos(abs(w))


def mean_imu(messages, field, axis):
    return statistics.fmean(getattr(getattr(message, field), axis) for message in messages)


def main(args=None):
    rclpy.init(args=args)
    node = CalibrationVerifier()
    passed = 0
    total = 8
    try:
        node.collect()

        raw_lidar_ok = (
            node.raw_lidar is not None
            and node.raw_lidar.header.frame_id == "mid360_link"
            and len(node.raw_lidar.data) > 0
        )
        passed += report(raw_lidar_ok, "raw lidar data remains available in mid360_link")

        calibrated_lidar_ok = (
            node.calibrated_lidar is not None
            and node.calibrated_lidar.header.frame_id == "mid360_calibrated"
            and len(node.calibrated_lidar.data) > 0
        )
        passed += report(calibrated_lidar_ok, "calibrated lidar topic publishes PointCloud2 data")

        transform = node.calibrated_transform()
        if transform is None:
            translation_error = math.inf
            angle_error = math.inf
        else:
            t = transform.transform.translation
            translation_error = math.sqrt(t.x ** 2 + t.y ** 2 + (t.z - 0.68) ** 2)
            angle_error = rotation_angle(transform.transform.rotation)
        passed += report(
            translation_error <= 0.02,
            f"lidar translation residual is {translation_error:.4f} m (limit 0.0200 m)",
        )
        passed += report(
            angle_error <= 0.02,
            f"lidar rotation residual is {angle_error:.4f} rad (limit 0.0200 rad)",
        )

        raw_imu_ok = node.raw_imu is not None and node.raw_imu.header.frame_id == "imu_link"
        passed += report(raw_imu_ok, "biased vendor IMU data remains available in imu_link")

        if len(node.corrected_imu) >= 100:
            gx = mean_imu(node.corrected_imu, "angular_velocity", "x")
            gy = mean_imu(node.corrected_imu, "angular_velocity", "y")
            gz = mean_imu(node.corrected_imu, "angular_velocity", "z")
            ax = mean_imu(node.corrected_imu, "linear_acceleration", "x")
            ay = mean_imu(node.corrected_imu, "linear_acceleration", "y")
            az = mean_imu(node.corrected_imu, "linear_acceleration", "z")
            imu_ok = max(abs(gx), abs(gy), abs(gz)) <= 0.008 and max(abs(ax), abs(ay)) <= 0.04 and abs(az - 9.81) <= 0.08
            imu_detail = f"gyro=({gx:.4f},{gy:.4f},{gz:.4f}), accel=({ax:.3f},{ay:.3f},{az:.3f})"
        else:
            imu_ok = False
            imu_detail = f"only {len(node.corrected_imu)}/100 corrected samples received"
        passed += report(imu_ok, f"corrected stationary IMU is within limits: {imu_detail}")

        image_ok = (
            node.camera_image is not None
            and node.camera_image.header.frame_id == "camera_optical_frame"
            and node.camera_image.width > 0
            and node.camera_image.height > 0
            and len(node.camera_image.data) > 0
        )
        passed += report(image_ok, "standard camera image topic carries valid optical-frame data")

        info_ok = (
            node.camera_info is not None
            and node.camera_info.header.frame_id == "camera_optical_frame"
            and node.camera_info.width > 0
            and node.camera_info.height > 0
        )
        passed += report(info_ok, "standard camera info topic carries valid optical-frame data")
    finally:
        node.destroy_node()
        rclpy.shutdown()

    print(f"\nResult: {passed}/{total} passed")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())

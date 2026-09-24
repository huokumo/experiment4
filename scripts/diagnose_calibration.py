#!/usr/bin/env python3

import math
import statistics
import time

import rclpy
from rclpy.duration import Duration
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from rclpy.time import Time
from sensor_msgs.msg import Image, Imu, PointCloud2
from tf2_ros import Buffer, TransformException, TransformListener


class CalibrationDiagnostics(Node):
    def __init__(self):
        super().__init__("diagnose_calibration")
        self._cloud = None
        self._camera_image = None
        self._imu_samples = []
        self._subscriptions = [
            self.create_subscription(
                PointCloud2,
                "/perception/lidar/points",
                self._receive_cloud,
                qos_profile_sensor_data,
            ),
            self.create_subscription(
                Imu,
                "/perception/imu/data",
                self._receive_imu,
                qos_profile_sensor_data,
            ),
            self.create_subscription(
                Image,
                "/perception/camera/image_raw",
                self._receive_image,
                qos_profile_sensor_data,
            ),
        ]
        self._tf_buffer = Buffer()
        self._tf_listener = TransformListener(self._tf_buffer, self)

    def _receive_cloud(self, message):
        self._cloud = message

    def _receive_imu(self, message):
        if len(self._imu_samples) < 200:
            self._imu_samples.append(message)

    def _receive_image(self, message):
        self._camera_image = message

    def collect(self, timeout_seconds=8.0):
        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            rclpy.spin_once(self, timeout_sec=0.1)
            if (
                self._cloud is not None
                and len(self._imu_samples) >= 100
                and self._camera_image is not None
            ):
                break

    def lidar_errors(self):
        try:
            transform = self._tf_buffer.lookup_transform(
                "base_link",
                "mid360_calibrated",
                Time(),
                timeout=Duration(seconds=1.0),
            )
        except TransformException:
            return math.inf, math.inf

        translation = transform.transform.translation
        translation_error = math.sqrt(
            translation.x ** 2
            + translation.y ** 2
            + (translation.z - 0.68) ** 2
        )
        rotation = transform.transform.rotation
        norm = math.sqrt(
            rotation.x ** 2
            + rotation.y ** 2
            + rotation.z ** 2
            + rotation.w ** 2
        )
        if norm == 0.0:
            return translation_error, math.inf
        w = max(-1.0, min(1.0, rotation.w / norm))
        return translation_error, 2.0 * math.acos(abs(w))


def mean_component(messages, field, axis):
    return statistics.fmean(
        getattr(getattr(message, field), axis) for message in messages
    )


def main(args=None):
    rclpy.init(args=args)
    node = CalibrationDiagnostics()
    try:
        node.collect()
        issues = 0
        print("\n=== Experiment 4: current calibration status ===", flush=True)

        translation_error, rotation_error = node.lidar_errors()
        lidar_ok = (
            node._cloud is not None
            and translation_error <= 0.02
            and rotation_error <= 0.02
        )
        if lidar_ok:
            print(
                f"[OK] Lidar extrinsic: translation={translation_error:.4f} m, "
                f"rotation={rotation_error:.4f} rad",
                flush=True,
            )
        else:
            issues += 1
            print(
                f"[ISSUE] Lidar extrinsic is misaligned: translation={translation_error:.4f} m, "
                f"rotation={rotation_error:.4f} rad",
                flush=True,
            )

        if len(node._imu_samples) >= 100:
            gx = mean_component(node._imu_samples, "angular_velocity", "x")
            gy = mean_component(node._imu_samples, "angular_velocity", "y")
            gz = mean_component(node._imu_samples, "angular_velocity", "z")
            ax = mean_component(node._imu_samples, "linear_acceleration", "x")
            ay = mean_component(node._imu_samples, "linear_acceleration", "y")
            imu_ok = max(abs(gx), abs(gy), abs(gz)) <= 0.008 and max(abs(ax), abs(ay)) <= 0.04
            imu_detail = f"gyro=({gx:.4f},{gy:.4f},{gz:.4f}), horizontal_accel=({ax:.3f},{ay:.3f})"
        else:
            imu_ok = False
            imu_detail = f"only {len(node._imu_samples)}/100 samples received"
        if imu_ok:
            print(f"[OK] Corrected stationary IMU: {imu_detail}", flush=True)
        else:
            issues += 1
            print(f"[ISSUE] Corrected stationary IMU still contains bias: {imu_detail}", flush=True)

        if node._camera_image is not None:
            print("[OK] Standard camera interface is publishing image data", flush=True)
        else:
            issues += 1
            print(
                "[ISSUE] Standard camera interface has no image data; check the adapter input topics",
                flush=True,
            )

        print(f"Current result: {issues} issue(s) remaining", flush=True)
        print("================================================\n", flush=True)
    finally:
        node.destroy_node()
        rclpy.try_shutdown()
    return 0


if __name__ == "__main__":
    main()

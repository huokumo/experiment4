#!/usr/bin/env python3

import math
import sys
import time

import rclpy
from rclpy.duration import Duration
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from rclpy.time import Time
from sensor_msgs.msg import PointCloud2
from tf2_ros import Buffer, TransformException, TransformListener


EXPECTED_XYZ = (0.0, 0.0, 0.68)
TRANSLATION_LIMIT = 0.02
ROTATION_LIMIT = 0.02


class LidarExtrinsicEvaluator(Node):
    def __init__(self):
        super().__init__("evaluate_lidar_extrinsic")
        self.cloud = None
        self.subscription = self.create_subscription(
            PointCloud2,
            "/perception/lidar/points",
            self.receive_cloud,
            qos_profile_sensor_data,
        )
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

    def receive_cloud(self, message):
        self.cloud = message

    def wait_for_data(self, timeout_seconds=10.0):
        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            rclpy.spin_once(self, timeout_sec=0.2)
            if self.cloud is None:
                continue
            try:
                return self.tf_buffer.lookup_transform(
                    "base_link",
                    "mid360_calibrated",
                    Time(),
                    timeout=Duration(seconds=0.2),
                )
            except TransformException:
                pass
        return None


def quaternion_angle(rotation):
    norm = math.sqrt(rotation.x ** 2 + rotation.y ** 2 + rotation.z ** 2 + rotation.w ** 2)
    if norm == 0.0:
        return math.inf
    normalized_w = max(-1.0, min(1.0, rotation.w / norm))
    return 2.0 * math.acos(abs(normalized_w))


def main(args=None):
    rclpy.init(args=args)
    node = LidarExtrinsicEvaluator()
    passed = False
    try:
        transform = node.wait_for_data()
        if transform is None:
            print("[FAIL] calibrated point cloud or transform is unavailable")
            return 1

        translation = transform.transform.translation
        actual_xyz = (translation.x, translation.y, translation.z)
        translation_error = math.sqrt(sum((a - b) ** 2 for a, b in zip(actual_xyz, EXPECTED_XYZ)))
        rotation_error = quaternion_angle(transform.transform.rotation)
        frame_ok = node.cloud.header.frame_id == "mid360_calibrated"
        passed = (
            frame_ok
            and translation_error <= TRANSLATION_LIMIT
            and rotation_error <= ROTATION_LIMIT
        )
        print(f"Cloud frame: {node.cloud.header.frame_id}")
        print("Current xyz: [{:.4f}, {:.4f}, {:.4f}]".format(*actual_xyz))
        print(f"Translation residual: {translation_error:.4f} m (limit {TRANSLATION_LIMIT:.3f} m)")
        print(f"Rotation residual: {rotation_error:.4f} rad (limit {ROTATION_LIMIT:.3f} rad)")
        print("[PASS] lidar extrinsic meets the acceptance limits" if passed else "[FAIL] adjust xyz/rpy and restart the launch file")
    finally:
        node.destroy_node()
        rclpy.shutdown()
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())

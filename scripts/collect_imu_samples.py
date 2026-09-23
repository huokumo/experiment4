#!/usr/bin/env python3

import csv
import sys
import time
from pathlib import Path

import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Imu


class ImuSampleCollector(Node):
    def __init__(self):
        super().__init__("collect_imu_samples")
        self.declare_parameter("topic", "/vendor/imu/data_raw")
        self.declare_parameter("sample_count", 500)
        self.declare_parameter("output_file", "/tmp/imu_samples.csv")
        self.declare_parameter("timeout_seconds", 20.0)

        self.target_count = int(self.get_parameter("sample_count").value)
        self.output_file = Path(self.get_parameter("output_file").value)
        self.timeout_seconds = float(self.get_parameter("timeout_seconds").value)
        self.samples = []
        self.done = False
        topic = self.get_parameter("topic").value
        self.subscription = self.create_subscription(
            Imu, topic, self.receive_sample, qos_profile_sensor_data
        )
        self.get_logger().info(
            f"Keep the robot stationary. Collecting {self.target_count} samples from {topic}."
        )

    def receive_sample(self, message):
        if self.done:
            return
        self.samples.append([
            message.angular_velocity.x,
            message.angular_velocity.y,
            message.angular_velocity.z,
            message.linear_acceleration.x,
            message.linear_acceleration.y,
            message.linear_acceleration.z,
        ])
        if len(self.samples) >= self.target_count:
            self.write_samples()

    def write_samples(self):
        self.output_file.parent.mkdir(parents=True, exist_ok=True)
        with self.output_file.open("w", newline="", encoding="utf-8") as output:
            writer = csv.writer(output)
            writer.writerow(["angular_x", "angular_y", "angular_z", "linear_x", "linear_y", "linear_z"])
            writer.writerows(self.samples)
        self.done = True
        self.get_logger().info(f"Saved {len(self.samples)} samples to {self.output_file}")


def main(args=None):
    rclpy.init(args=args)
    node = ImuSampleCollector()
    deadline = time.monotonic() + node.timeout_seconds
    exit_code = 0
    try:
        while rclpy.ok() and not node.done and time.monotonic() < deadline:
            rclpy.spin_once(node, timeout_sec=0.2)
        if not node.done:
            node.get_logger().error(
                f"Timed out after receiving {len(node.samples)}/{node.target_count} samples"
            )
            exit_code = 1
    except KeyboardInterrupt:
        exit_code = 130
    finally:
        node.destroy_node()
        rclpy.shutdown()
    return exit_code


if __name__ == "__main__":
    sys.exit(main())

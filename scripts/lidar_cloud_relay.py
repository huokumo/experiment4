#!/usr/bin/env python3

import math

import rclpy
from geometry_msgs.msg import TransformStamped
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import PointCloud2
from tf2_ros import StaticTransformBroadcaster


def quaternion_from_euler(roll, pitch, yaw):
    cr = math.cos(roll * 0.5)
    sr = math.sin(roll * 0.5)
    cp = math.cos(pitch * 0.5)
    sp = math.sin(pitch * 0.5)
    cy = math.cos(yaw * 0.5)
    sy = math.sin(yaw * 0.5)
    return (
        sr * cp * cy - cr * sp * sy,
        cr * sp * cy + sr * cp * sy,
        cr * cp * sy - sr * sp * cy,
        cr * cp * cy + sr * sp * sy,
    )


class LidarCloudRelay(Node):
    def __init__(self):
        super().__init__("lidar_cloud_relay")
        self.declare_parameter("input_topic", "/mid360/points")
        self.declare_parameter("output_topic", "/perception/lidar/points")
        self.declare_parameter("parent_frame", "base_link")
        self.declare_parameter("calibrated_frame", "mid360_calibrated")
        self.declare_parameter("xyz", [0.05, 0.0, 0.73])
        self.declare_parameter("rpy", [0.0, 0.0, 0.12])

        input_topic = self.get_parameter("input_topic").value
        output_topic = self.get_parameter("output_topic").value
        self.calibrated_frame = self.get_parameter("calibrated_frame").value

        self.publisher = self.create_publisher(PointCloud2, output_topic, 10)
        self.subscription = self.create_subscription(
            PointCloud2, input_topic, self.relay_cloud, qos_profile_sensor_data
        )
        self.tf_broadcaster = StaticTransformBroadcaster(self)
        self.publish_calibrated_transform()
        self.get_logger().info(
            f"Relaying {input_topic} to {output_topic} in frame {self.calibrated_frame}"
        )

    def publish_calibrated_transform(self):
        xyz = [float(value) for value in self.get_parameter("xyz").value]
        rpy = [float(value) for value in self.get_parameter("rpy").value]
        if len(xyz) != 3 or len(rpy) != 3:
            raise ValueError("xyz and rpy must each contain three values")

        transform = TransformStamped()
        transform.header.stamp = self.get_clock().now().to_msg()
        transform.header.frame_id = self.get_parameter("parent_frame").value
        transform.child_frame_id = self.calibrated_frame
        transform.transform.translation.x = xyz[0]
        transform.transform.translation.y = xyz[1]
        transform.transform.translation.z = xyz[2]
        qx, qy, qz, qw = quaternion_from_euler(*rpy)
        transform.transform.rotation.x = qx
        transform.transform.rotation.y = qy
        transform.transform.rotation.z = qz
        transform.transform.rotation.w = qw
        self.tf_broadcaster.sendTransform(transform)

    def relay_cloud(self, message):
        message.header.frame_id = self.calibrated_frame
        self.publisher.publish(message)


def main(args=None):
    rclpy.init(args=args)
    node = LidarCloudRelay()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == "__main__":
    main()

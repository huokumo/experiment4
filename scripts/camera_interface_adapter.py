#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import CameraInfo, Image


class CameraInterfaceAdapter(Node):
    def __init__(self):
        super().__init__("camera_interface_adapter")
        self.declare_parameter("image_input", "/wrong/image")
        self.declare_parameter("image_output", "/perception/camera/image_raw")
        self.declare_parameter("info_input", "/wrong/info")
        self.declare_parameter("info_output", "/perception/camera/camera_info")

        image_input = self.get_parameter("image_input").value
        image_output = self.get_parameter("image_output").value
        info_input = self.get_parameter("info_input").value
        info_output = self.get_parameter("info_output").value

        self.image_publisher = self.create_publisher(Image, image_output, 10)
        self.info_publisher = self.create_publisher(CameraInfo, info_output, 10)
        self.image_subscription = self.create_subscription(
            Image, image_input, self.image_publisher.publish, qos_profile_sensor_data
        )
        self.info_subscription = self.create_subscription(
            CameraInfo, info_input, self.info_publisher.publish, qos_profile_sensor_data
        )
        self.get_logger().info(f"Camera adapter: {image_input} -> {image_output}")
        self.get_logger().info(f"Camera adapter: {info_input} -> {info_output}")


def main(args=None):
    rclpy.init(args=args)
    node = CameraInterfaceAdapter()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == "__main__":
    main()

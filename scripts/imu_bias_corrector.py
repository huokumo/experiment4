#!/usr/bin/env python3

import copy

import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Imu


class ImuBiasCorrector(Node):
    def __init__(self):
        super().__init__("imu_bias_corrector")
        self.declare_parameter("input_topic", "/vendor/imu/data_raw")
        self.declare_parameter("output_topic", "/perception/imu/data")
        self.declare_parameter("angular_velocity_bias", [0.0, 0.0, 0.0])
        self.declare_parameter("linear_acceleration_bias", [0.0, 0.0, 0.0])

        input_topic = self.get_parameter("input_topic").value
        output_topic = self.get_parameter("output_topic").value
        self.angular_bias = self.read_vector("angular_velocity_bias")
        self.linear_bias = self.read_vector("linear_acceleration_bias")
        self.publisher = self.create_publisher(Imu, output_topic, qos_profile_sensor_data)
        self.subscription = self.create_subscription(
            Imu, input_topic, self.correct_bias, qos_profile_sensor_data
        )
        self.get_logger().info(f"Publishing corrected IMU data on {output_topic}")

    def read_vector(self, name):
        values = [float(value) for value in self.get_parameter(name).value]
        if len(values) != 3:
            raise ValueError(f"{name} must contain three values")
        return values

    def correct_bias(self, message):
        output = copy.deepcopy(message)
        output.angular_velocity.x -= self.angular_bias[0]
        output.angular_velocity.y -= self.angular_bias[1]
        output.angular_velocity.z -= self.angular_bias[2]
        output.linear_acceleration.x -= self.linear_bias[0]
        output.linear_acceleration.y -= self.linear_bias[1]
        output.linear_acceleration.z -= self.linear_bias[2]
        self.publisher.publish(output)


def main(args=None):
    rclpy.init(args=args)
    node = ImuBiasCorrector()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()

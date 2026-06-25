#!/usr/bin/env python3
"""
将 robot_description 参数发布到 /robot_description 话题（latched）。

RViz2 的 RobotModel 显示插件从话题读取 URDF，而 robot_state_publisher
仅将其设为参数，需要此节点完成参数→话题的转发。
"""
import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class RobotDescriptionPublisher(Node):
    def __init__(self):
        super().__init__('robot_description_publisher')
        self.declare_parameter('robot_description', '')
        robot_desc = self.get_parameter('robot_description').value

        if not robot_desc:
            self.get_logger().error('robot_description 参数为空！无法发布。')
            return

        # latched publisher: transient_local 确保后来的订阅者也能收到
        qos = rclpy.qos.QoSProfile(
            depth=1,
            durability=rclpy.qos.DurabilityPolicy.TRANSIENT_LOCAL,
        )
        self.pub = self.create_publisher(String, 'robot_description', qos)
        self.pub.publish(String(data=robot_desc))
        self.get_logger().info('robot_description 已发布到话题（latched）')


def main():
    rclpy.init()
    node = RobotDescriptionPublisher()
    rclpy.spin(node)


if __name__ == '__main__':
    main()

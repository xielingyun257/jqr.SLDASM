#!/usr/bin/env python3
"""
将 robot_description 参数发布到 /rviz_robot_description 话题（latched + 定时重发）。

设计要点：
  - 使用独立话题 /rviz_robot_description，不与 /robot_description 冲突
  - joint_state_publisher_gui 订阅的是 /robot_description，不受影响
  - RViz2 配置指向 /rviz_robot_description，支持定时重发保证可靠性
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

        qos = rclpy.qos.QoSProfile(
            depth=1,
            durability=rclpy.qos.DurabilityPolicy.TRANSIENT_LOCAL,
            reliability=rclpy.qos.ReliabilityPolicy.RELIABLE,
        )
        self.msg = String(data=robot_desc)

        # 发布到 /robot_description（joint_state_publisher 需要）
        self.pub_rd = self.create_publisher(String, '/robot_description', qos)
        # 发布到 /rviz_robot_description（RViz2 需要，独立话题）
        self.pub_rviz = self.create_publisher(String, '/rviz_robot_description', qos)

        # 定期重发（确保晚加入的订阅者能收到）
        self.timer = self.create_timer(3.0, self._publish_callback)
        # 立即尝试发布（spin 后会真正发出）
        self._publish_callback()
        self.get_logger().info('robot_description 已发布到 /robot_description + /rviz_robot_description')

    def _publish_callback(self):
        self.pub_rd.publish(self.msg)
        self.pub_rviz.publish(self.msg)


def main():
    rclpy.init()
    node = RobotDescriptionPublisher()
    rclpy.spin(node)


if __name__ == '__main__':
    main()

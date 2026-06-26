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

        # /rviz_robot_description：RViz2 加载模型用
        self.pub_rviz = self.create_publisher(String, '/rviz_robot_description', qos)
        self.pub_rviz.publish(self.msg)

        # /robot_description：给 joint_state_publisher_gui 初始化用
        # 延迟 1 秒发一次（等 GUI 订阅就绪），之后不再重发（否则 GUI 重置归零）
        self.pub_rd = self.create_publisher(String, '/robot_description', qos)
        self.pub_rd.publish(self.msg)
        self._retry_count = 0
        self._retry_timer = self.create_timer(1.0, self._retry_robot_desc)

        self.get_logger().info('robot_description 已发布（/rviz_robot_description + /robot_description 各一次）')

    def _retry_robot_desc(self):
        self._retry_count += 1
        if self._retry_count <= 2:
            self.pub_rd.publish(self.msg)
        else:
            self._retry_timer.cancel()  # 停掉定时器，不再重发


def main():
    rclpy.init()
    node = RobotDescriptionPublisher()
    rclpy.spin(node)


if __name__ == '__main__':
    main()

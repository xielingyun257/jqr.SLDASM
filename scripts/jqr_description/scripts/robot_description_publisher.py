#!/usr/bin/env python3
"""
将 robot_description 参数发布到 /rviz_robot_description 话题。

设计要点：
  - /rviz_robot_description：持续定时重发（RViz2 加载模型，不会触发重置）
  - /robot_description：只在初始 3 秒内发 3 次，之后停止（joint_state_publisher_gui
    收到 /robot_description 会触发 centering 归零，不能持续重发）
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

        self.pub_rviz = self.create_publisher(String, '/rviz_robot_description', qos)
        self.pub_rd = self.create_publisher(String, '/robot_description', qos)

        # 立即发一次
        self.pub_rviz.publish(self.msg)
        self.pub_rd.publish(self.msg)

        # 定时器：/rviz_robot_description 持续重发，/robot_description 前3次后停
        self._tick = 0
        self.timer = self.create_timer(1.0, self._on_timer)

        self.get_logger().info('robot_description 发布器就绪')

    def _on_timer(self):
        self._tick += 1
        # /rviz_robot_description 持续重发，确保 RViz2 加载模型
        self.pub_rviz.publish(self.msg)
        # /robot_description 只在前 3 秒发，避免触发 GUI 滑块归零
        if self._tick <= 3:
            self.pub_rd.publish(self.msg)
        elif self._tick == 4:
            self.get_logger().info('/robot_description 已停止重发（防止滑块归零）')


def main():
    rclpy.init()
    node = RobotDescriptionPublisher()
    rclpy.spin(node)


if __name__ == '__main__':
    main()

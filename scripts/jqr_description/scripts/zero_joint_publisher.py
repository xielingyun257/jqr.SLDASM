#!/usr/bin/env python3
"""发布 13 个关节的零位状态，供 robot_state_publisher 构建 TF 树"""
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState

JOINTS = [
    'joint_1',
    'joint_l_2', 'joint_l_3', 'joint_l_4', 'joint_l_5', 'joint_l_6', 'joint_l_7',
    'joint_r_2', 'joint_r_3', 'joint_r_4', 'joint_r_5', 'joint_r_6', 'joint_r_7',
]


class ZeroJointPublisher(Node):
    def __init__(self):
        super().__init__('zero_joint_publisher')
        self.pub = self.create_publisher(JointState, '/joint_states', 10)
        self.timer = self.create_timer(0.5, self._publish)
        self.get_logger().info('零位关节状态发布器已启动（13 关节）')

    def _publish(self):
        msg = JointState()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.name = JOINTS
        msg.position = [0.0] * len(JOINTS)
        self.pub.publish(msg)


def main():
    rclpy.init()
    node = ZeroJointPublisher()
    rclpy.spin(node)


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""ROS2 /joint_states → Ignition Gazebo 关节命令桥接"""
import subprocess, threading, time
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState

JOINTS = ['joint_1','joint_l_2','joint_l_3','joint_l_4','joint_l_5','joint_l_6','joint_l_7',
          'joint_r_2','joint_r_3','joint_r_4','joint_r_5','joint_r_6','joint_r_7']

current = {j: 0.0 for j in JOINTS}
lock = threading.Lock()
changed = threading.Event()

class Bridge(Node):
    def __init__(self):
        super().__init__('gz_bridge')
        self.sub = self.create_subscription(JointState, '/joint_states', self._cb, 10)
    def _cb(self, msg):
        global current, changed
        with lock:
            for n, p in zip(msg.name, msg.position):
                if n in current and abs(current[n] - p) > 0.001:
                    current[n] = float(p)
                    changed.set()

def gz_sender():
    """发送线程：每 100ms 检查并发送变化的关节到 Gazebo"""
    while True:
        if changed.wait(timeout=0.1):
            changed.clear()
            with lock:
                snap = dict(current)
            # 批量发送
            for jn, val in snap.items():
                subprocess.run(
                    ['ign', 'topic', '-t', f'/model/jqr/joint/{jn}/0/cmd_pos',
                     '-m', 'ignition.msgs.Double', '-p', f'data: {val}'],
                    capture_output=True, timeout=3)
            time.sleep(0.05)  # 限流

rclpy.init()
bridge = Bridge()
t = threading.Thread(target=gz_sender, daemon=True)
t.start()
bridge.get_logger().info('Gazebo 关节桥接已启动')
rclpy.spin(bridge)

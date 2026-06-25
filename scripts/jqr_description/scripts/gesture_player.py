#!/usr/bin/env python3
"""
jqr 交通指挥手势播放节点

功能：
  - 加载 YAML 手势文件
  - 通过 FollowJointTrajectory Action 发送到 joint_trajectory_controller
  - 支持键盘交互选择手势（1-8）或循环播放

用法：
  ros2 run jqr_description gesture_player.py
  ros2 run jqr_description gesture_player.py --ros-args -p gesture_dir:=/path/to/gestures
"""

import os
import sys
import time
import json
import select
import termios
import tty

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from control_msgs.action import FollowJointTrajectory
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from builtin_interfaces.msg import Duration

# 13 个关节名（与 URDF 一致）
JOINT_NAMES = [
    'joint_1',
    'joint_l_2', 'joint_l_3', 'joint_l_4', 'joint_l_5', 'joint_l_6', 'joint_l_7',
    'joint_r_2', 'joint_r_3', 'joint_r_4', 'joint_r_5', 'joint_r_6', 'joint_r_7',
]

GESTURE_FILES = {
    '1': 'stop.json',
    '2': 'go_straight.json',
    '3': 'left_turn.json',
    '4': 'right_turn.json',
    '5': 'slow_down.json',
    '6': 'pull_over.json',
    '7': 'lane_change.json',
    '8': 'wait_turn.json',
}

MENU = """
╔══════════════════════════════════════╗
║    jqr 交通指挥手势播放器            ║
╠══════════════════════════════════════╣
║  1 - 停止信号    (Stop)              ║
║  2 - 直行信号    (Go Straight)       ║
║  3 - 左转弯信号  (Left Turn)         ║
║  4 - 右转弯信号  (Right Turn)        ║
║  5 - 减速信号    (Slow Down)         ║
║  6 - 靠边停车    (Pull Over)         ║
║  7 - 变道信号    (Lane Change)       ║
║  8 - 待转信号    (Wait to Turn)      ║
╠══════════════════════════════════════╣
║  0 - 归零所有关节                    ║
║  L - 循环播放全部手势                ║
║  Q - 退出                            ║
╚══════════════════════════════════════╝
选择手势 [1-8, 0, L, Q]: """


class GesturePlayer(Node):
    def __init__(self):
        super().__init__('gesture_player')

        self.declare_parameter('gesture_dir', '')
        self.gesture_dir = self.get_parameter('gesture_dir').value

        if not self.gesture_dir:
            # 默认从包共享目录下的 gestures 加载
            from ament_index_python.packages import get_package_share_directory
            self.gesture_dir = os.path.join(
                get_package_share_directory('jqr_description'), 'gestures'
            )

        self.get_logger().info(f'手势文件目录: {self.gesture_dir}')

        # Action 客户端
        self._action_client = ActionClient(
            self, FollowJointTrajectory,
            '/joint_trajectory_controller/follow_joint_trajectory'
        )

        # 加载所有手势
        self.gestures = {}
        for key, filename in GESTURE_FILES.items():
            filepath = os.path.join(self.gesture_dir, filename)
            self.gestures[key] = self._load_gesture(filepath)

        self.get_logger().info(f'已加载 {len(self.gestures)} 个手势')

    def _load_gesture(self, filepath: str) -> dict:
        """加载 JSON 手势文件"""
        with open(filepath, 'r') as f:
            data = json.load(f)
        self.get_logger().info(f'  加载: {data["name"]} ← {os.path.basename(filepath)}')
        return data

    def _build_trajectory(self, gesture: dict) -> JointTrajectory:
        """从手势数据构建 JointTrajectory 消息"""
        traj = JointTrajectory()
        traj.joint_names = gesture['joint_names']

        for pt in gesture['trajectory']:
            point = JointTrajectoryPoint()
            point.positions = pt['positions']
            t = pt['time']
            point.time_from_start = Duration(sec=int(t), nanosec=int((t - int(t)) * 1e9))
            traj.points.append(point)

        return traj

    def send_gesture(self, key: str) -> bool:
        """发送手势轨迹"""
        if key == '0':
            return self._send_zero()

        if key not in self.gestures:
            self.get_logger().error(f'未知手势: {key}')
            return False

        gesture = self.gestures[key]
        traj = self._build_trajectory(gesture)

        self.get_logger().info(f'发送手势: {gesture["name"]} ({len(traj.points)} 个路径点)')

        # 等待 action server
        if not self._action_client.wait_for_server(timeout_sec=5.0):
            self.get_logger().error('无法连接 joint_trajectory_controller Action Server！')
            self.get_logger().error('请先启动控制器: ros2 launch jqr_description traffic_gesture.launch.py')
            return False

        goal = FollowJointTrajectory.Goal()
        goal.trajectory = traj

        future = self._action_client.send_goal_async(goal)
        rclpy.spin_until_future_complete(self, future)

        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().error('手势执行请求被拒绝')
            return False

        self.get_logger().info('手势执行中...')

        result_future = goal_handle.get_result_async()
        rclpy.spin_until_future_complete(self, result_future)

        result = result_future.result()
        if result.result.error_code == 0:
            self.get_logger().info(f'手势 {gesture["name"]} 执行完成')
            return True
        else:
            self.get_logger().error(f'执行失败: {result.result.error_string}')
            return False

    def _send_zero(self) -> bool:
        """所有关节归零"""
        traj = JointTrajectory()
        traj.joint_names = JOINT_NAMES
        point = JointTrajectoryPoint()
        point.positions = [0.0] * len(JOINT_NAMES)
        point.time_from_start = Duration(sec=2, nanosec=0)
        traj.points.append(point)

        if not self._action_client.wait_for_server(timeout_sec=5.0):
            self.get_logger().error('无法连接 joint_trajectory_controller！')
            return False

        goal = FollowJointTrajectory.Goal()
        goal.trajectory = traj
        self._action_client.send_goal_async(goal)
        self.get_logger().info('归零中...')
        return True

    def loop_all(self):
        """循环播放全部 8 个手势"""
        self.get_logger().info('开始循环播放全部手势 (Ctrl+C 停止)')
        try:
            while rclpy.ok():
                for key in ['1', '2', '3', '4', '5', '6', '7', '8']:
                    self.send_gesture(key)
                    time.sleep(1.0)  # 手势间隔
        except KeyboardInterrupt:
            self.get_logger().info('循环播放已停止')


def get_key() -> str:
    """非阻塞读取键盘输入"""
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        if select.select([sys.stdin], [], [], 0.1)[0]:
            return sys.stdin.read(1).upper()
        return ''
    finally:
        termios.tcsetattr(fd, old_settings)


def main():
    rclpy.init()

    player = GesturePlayer()

    print(MENU)

    try:
        while rclpy.ok():
            rclpy.spin_once(player, timeout_sec=0.1)

            key = get_key()
            if not key:
                continue

            if key == 'Q':
                print('\n退出。')
                break
            elif key == 'L':
                player.loop_all()
                print(MENU)
            elif key in GESTURE_FILES or key == '0':
                player.send_gesture(key)
                print(MENU)
            elif key:
                print(f'无效选项: {key}')
                print(MENU)

    except KeyboardInterrupt:
        print('\n中断。')
    finally:
        player.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
jqr 手势演示 — 统一驱动 Gazebo + RViz2

- /joint_states: 50Hz 发布（给 robot_state_publisher → TF → RViz2）
- Gazebo JointTrajectoryController: 每个手势发送一条完整轨迹（Gazebo 内部插值执行）

用法:
  python3 gesture_demo.py
"""
import json, os, subprocess, sys, time
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from ament_index_python.packages import get_package_share_directory

JOINTS = ['joint_1','joint_l_2','joint_l_3','joint_l_4','joint_l_5','joint_l_6','joint_l_7',
          'joint_r_2','joint_r_3','joint_r_4','joint_r_5','joint_r_6','joint_r_7']

GESTURE_FILES = ['stop','go_straight','left_turn','right_turn',
                 'slow_down','pull_over','lane_change','wait_turn']


def gesture_to_traj_parts(gesture):
    """将手势 JSON 转为 subprocess.run 参数列表（JointTrajectory 消息）"""
    pts = gesture['trajectory']

    # 构建 protobuf 文本（和手动测试完全一致的格式）
    msg = ' '.join([f'joint_names: "{jn}"' for jn in JOINTS])

    step = max(1, len(pts) // 50)
    idx_list = list(range(0, len(pts), step))
    if (len(pts) - 1) % step != 0:
        idx_list.append(len(pts) - 1)

    for i in idx_list:
        p = pts[i]
        t = p['time']
        msg += ' points { ' + ' '.join([f'positions: {pos}' for pos in p['positions']])
        msg += f' time_from_start {{ sec: {int(t)} nsec: {int((t-int(t))*1e9)} }} }}'

    return ['ign', 'topic', '-t', '/model/jqr/joint_trajectory',
            '-m', 'ignition.msgs.JointTrajectory', '-p', msg]


def gesture_to_traj_cmd(gesture):
    """将手势 JSON 转为 ign topic 命令字符串（JointTrajectory 消息）"""
    pts = gesture['trajectory']

    # 用和手动测试完全一致的格式：单引号包裹，无换行
    cmd = "ign topic -t '/model/jqr/joint_trajectory' -m ignition.msgs.JointTrajectory -p '"

    # joint_names（一行）
    cmd += ' '.join([f'joint_names: "{jn}"' for jn in JOINTS])

    # trajectory points
    step = max(1, len(pts) // 50)
    idx_list = list(range(0, len(pts), step))
    if (len(pts) - 1) % step != 0:
        idx_list.append(len(pts) - 1)

    for i in idx_list:
        p = pts[i]
        t = p['time']
        cmd += ' points { ' + ' '.join([f'positions: {pos}' for pos in p['positions']])
        cmd += f' time_from_start {{ sec: {int(t)} nsec: {int((t-int(t))*1e9)} }} }}'

    cmd += "'"
    return cmd


class GestureDemo(Node):
    def __init__(self, gesture_dir):
        super().__init__('gesture_demo')
        self.pub = self.create_publisher(JointState, '/joint_states', 10)

        # 加载手势
        self.gestures = []
        for f in GESTURE_FILES:
            p = os.path.join(gesture_dir, f'{f}.json')
            with open(p) as fp:
                self.gestures.append(json.load(fp))
        self.get_logger().info(f'加载 {len(self.gestures)} 个手势')

    def _pub_js(self, positions):
        msg = JointState()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.name = JOINTS
        msg.position = [float(p) for p in positions]
        self.pub.publish(msg)

    def _spin(self, dt):
        t0 = time.perf_counter()
        rclpy.spin_once(self, timeout_sec=0.001)
        elapsed = time.perf_counter() - t0
        if elapsed < dt:
            time.sleep(dt - elapsed)

    def run(self):
        cycle = 0.02  # 50Hz

        # 零位初始化 2 秒
        self.get_logger().info('初始化零位...')
        t_start = self.get_clock().now()
        while (self.get_clock().now() - t_start).nanoseconds / 1e9 < 2.0:
            self._pub_js([0.0]*13)
            self._spin(cycle)
        self.get_logger().info('零位就绪')

        # 循环播放
        round_num = 0
        while rclpy.ok():
            round_num += 1
            self.get_logger().info(f'=== 第 {round_num} 轮 ===')

            for gi, g in enumerate(self.gestures):
                name = g['name']
                dur = g['trajectory'][-1]['time']
                self.get_logger().info(f'[{gi+1}/8] {name} ({dur:.1f}s)')

                # 1. 发送完整轨迹到 Gazebo（list args，避免 shell 解析问题）
                cmd_parts = gesture_to_traj_parts(g)
                self.get_logger().info(f'  发送轨迹到 Gazebo ({len(cmd_parts[-1])} 字符)...')
                t0 = time.perf_counter()
                subprocess.run(cmd_parts, capture_output=True, timeout=5)
                elapsed = time.perf_counter() - t0
                self.get_logger().info(f'  发送完成 ({elapsed:.1f}s)')

                # 2. 同时发布 /joint_states（给 RViz2）
                t_gesture = self.get_clock().now()
                t_elapsed = 0.0
                last_pos = [0.0]*13

                while t_elapsed < dur + 0.5:
                    now = self.get_clock().now()
                    t_elapsed = (now - t_gesture).nanoseconds / 1e9
                    pos = self._interp(g['trajectory'], min(t_elapsed, dur))
                    if pos != last_pos:
                        self._pub_js(pos)
                        last_pos = list(pos)
                    self._spin(cycle)

                # 手势间停顿 0.5s
                t_pause = self.get_clock().now()
                while (self.get_clock().now() - t_pause).nanoseconds / 1e9 < 0.5:
                    self._pub_js(last_pos)
                    self._spin(cycle)

            # 轮间停顿 1s
            t_pause = self.get_clock().now()
            while (self.get_clock().now() - t_pause).nanoseconds / 1e9 < 1.0:
                self._pub_js(last_pos)
                self._spin(cycle)

    def _interp(self, pts, t):
        if len(pts) == 1:
            return list(pts[0]['positions'])
        for i in range(len(pts)-1):
            t0 = pts[i]['time']
            t1 = pts[i+1]['time']
            if t0 <= t <= t1:
                frac = (t - t0) / (t1 - t0) if t1 > t0 else 0
                p0 = pts[i]['positions']
                p1 = pts[i+1]['positions']
                return [p0[j] + frac*(p1[j]-p0[j]) for j in range(len(p0))]
        return list(pts[-1]['positions'])


def main():
    rclpy.init()
    gd = os.path.join(get_package_share_directory('jqr_description'), 'gestures')
    node = GestureDemo(gd)
    node.run()
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()

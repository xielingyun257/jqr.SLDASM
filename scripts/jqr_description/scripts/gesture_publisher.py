#!/usr/bin/env python3
"""jqr 手势播放器 — 直接发布 /joint_states（同时驱动 Gazebo + RViz2）"""

import json, os, sys, time
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from ament_index_python.packages import get_package_share_directory

JOINTS = ['joint_1','joint_l_2','joint_l_3','joint_l_4','joint_l_5','joint_l_6','joint_l_7',
          'joint_r_2','joint_r_3','joint_r_4','joint_r_5','joint_r_6','joint_r_7']

class GesturePlayer(Node):
    def __init__(self, gesture_dir):
        super().__init__('gesture_player')
        self.pub = self.create_publisher(JointState, '/joint_states', 10)
        self.gesture_dir = gesture_dir
        self.gestures = []
        for f in ['stop','go_straight','left_turn','right_turn',
                  'slow_down','pull_over','lane_change','wait_turn']:
            p = os.path.join(gesture_dir, f'{f}.json')
            with open(p) as fp:
                self.gestures.append(json.load(fp))

    def _pub(self, positions, now):
        msg = JointState()
        msg.header.stamp = now
        msg.name = JOINTS
        msg.position = [float(p) for p in positions]
        self.pub.publish(msg)

    def run(self):
        rate = self.create_rate(50)  # 50Hz
        start = self.get_clock().now()

        # 开机先发布 2 秒零位，确保 RViz2 和 Gazebo 从零位开始
        self.get_logger().info('初始化零位...')
        t0 = self.get_clock().now()
        while (self.get_clock().now() - t0).nanoseconds / 1e9 < 2.0:
            self._pub([0.0]*13, self.get_clock().now().to_msg())
            rate.sleep()
        self.get_logger().info('零位就绪，开始手势演示')

        for gi, g in enumerate(self.gestures):
            name = g['name']
            pts = g['trajectory']
            dur = pts[-1]['time']
            self.get_logger().info(f'[{gi+1}/8] {name} ({dur:.1f}s)')

            t0 = self.get_clock().now()
            t_elapsed = 0.0
            last_pos = [0.0]*13

            while t_elapsed < dur + 0.5:
                now = self.get_clock().now()
                t_elapsed = (now - t0).nanoseconds / 1e9

                # 找到当前段的插值区间
                positions = self._interp(pts, min(t_elapsed, dur))

                if positions != last_pos or abs(t_elapsed - dur) < 0.01:
                    self._pub(positions, now.to_msg())
                    last_pos = list(positions)

                rate.sleep()

            # 手势间停顿
            delay_end = self.get_clock().now()
            while (self.get_clock().now() - delay_end).nanoseconds / 1e9 < 0.5:
                self._pub(last_pos, self.get_clock().now().to_msg())
                rate.sleep()

        self.get_logger().info('✅ 8个手势全部完成！')

        # 回到零位
        t0 = self.get_clock().now()
        while (self.get_clock().now() - t0).nanoseconds / 1e9 < 2.0:
            now = self.get_clock().now()
            elapsed = (now - t0).nanoseconds / 1e9
            frac = min(elapsed / 1.5, 1.0)
            pos = [lp * (1-frac) for lp in last_pos]
            self._pub(pos, now.to_msg())
            rate.sleep()

    def _interp(self, pts, t):
        """在轨迹点之间线性插值"""
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
    print(f'手势目录: {gd}')
    node = GesturePlayer(gd)
    node.run()
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()

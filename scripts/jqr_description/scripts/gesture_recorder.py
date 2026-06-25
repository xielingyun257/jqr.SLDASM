#!/usr/bin/env python3
"""
jqr 手势录制器 — 点击按钮记录当前关节角度

用法：
  ros2 run jqr_description gesture_recorder.py

操作：
  1. 在 joint_state_publisher_gui 中拖滑块摆好手势姿态
  2. 点击对应手势按钮 → 自动记录 13 个关节角度
  3. 全部录完后点击"保存全部"→ 写入 gestures/*.json
  4. 点击"测试"可发送轨迹到控制器验证
"""

import os
import json
import threading
import tkinter as tk
from tkinter import ttk, messagebox

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from sensor_msgs.msg import JointState
from control_msgs.action import FollowJointTrajectory
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from builtin_interfaces.msg import Duration

JOINT_ORDER = [
    'joint_1',
    'joint_l_2', 'joint_l_3', 'joint_l_4', 'joint_l_5', 'joint_l_6', 'joint_l_7',
    'joint_r_2', 'joint_r_3', 'joint_r_4', 'joint_r_5', 'joint_r_6', 'joint_r_7',
]

GESTURES = [
    ('1', '停止', 'stop'),
    ('2', '直行', 'go_straight'),
    ('3', '左转弯', 'left_turn'),
    ('4', '右转弯', 'right_turn'),
    ('5', '减速慢行', 'slow_down'),
    ('6', '靠边停车', 'pull_over'),
    ('7', '变道', 'lane_change'),
    ('8', '待转', 'wait_turn'),
]

class GestureRecorder:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("jqr 手势录制器")
        self.root.geometry("550x520")
        self.root.resizable(False, False)

        # 当前关节位置
        self.current_positions = {}
        self.lock = threading.Lock()

        # 录制的数据 {gesture_key: [positions]}
        self.recorded = {}

        # === ROS2 节点（在单独线程运行） ===
        self.ros_node = None
        self.ros_ready = False
        self.ros_thread = threading.Thread(target=self._ros_spin, daemon=True)
        self.ros_thread.start()

        # === GUI ===
        self._build_ui()

        # 定时更新显示
        self.root.after(200, self._update_display)

    def _ros_spin(self):
        rclpy.init()
        self.ros_node = RecorderNode(self)
        self.ros_ready = True
        rclpy.spin(self.ros_node)

    def _build_ui(self):
        main = ttk.Frame(self.root, padding=10)
        main.pack(fill=tk.BOTH, expand=True)

        # 标题
        ttk.Label(main, text="jqr 双机械臂手势录制器",
                  font=('Arial', 14, 'bold')).pack(pady=5)
        ttk.Label(main, text="1. 在 GUI 中拖滑块摆好姿态 → 2. 点击按钮记录 → 3. 保存全部",
                  font=('Arial', 9)).pack(pady=2)

        # 当前关节角度显示
        display_frame = ttk.LabelFrame(main, text="当前关节角度 (实时)", padding=5)
        display_frame.pack(fill=tk.X, pady=5)

        self.joint_labels = {}
        for i, jn in enumerate(JOINT_ORDER):
            row = i // 2
            col = (i % 2) * 2
            lbl = ttk.Label(display_frame, text=f"{jn}:", width=9, anchor=tk.E)
            lbl.grid(row=row, column=col, sticky=tk.E, padx=2, pady=1)
            val = ttk.Label(display_frame, text=" ---", width=6, anchor=tk.W,
                            font=('Courier', 9))
            val.grid(row=row, column=col+1, sticky=tk.W, padx=2, pady=1)
            self.joint_labels[jn] = val

        # 手势按钮
        btn_frame = ttk.LabelFrame(main, text="点击记录手势", padding=8)
        btn_frame.pack(fill=tk.X, pady=5)

        self.rec_buttons = {}
        for i, (key, name, fname) in enumerate(GESTURES):
            row = i // 4
            col = i % 4
            btn = tk.Button(btn_frame, text=f"{key}. {name}", width=14, height=2,
                           bg='#e8e8e8', font=('Arial', 9, 'bold'),
                           command=lambda k=key, n=name: self.record(k, n))
            btn.grid(row=row, column=col, padx=3, pady=3)
            self.rec_buttons[key] = btn

        # 已录状态显示
        self.status_label = ttk.Label(
            main, text="已录: (无)", font=('Arial', 10), foreground='gray')
        self.status_label.pack(pady=3)

        # 操作按钮行
        op_frame = ttk.Frame(main)
        op_frame.pack(fill=tk.X, pady=8)

        tk.Button(op_frame, text="清空重录", bg='#ffaaaa', width=12, height=2,
                 command=self.clear).pack(side=tk.LEFT, padx=5)

        tk.Button(op_frame, text="保存全部", bg='#aaffaa', width=12, height=2,
                 command=self.save_all).pack(side=tk.LEFT, padx=5)

        tk.Button(op_frame, text="测试当前手势", bg='#aaaaff', width=14, height=2,
                 command=self.test_gesture).pack(side=tk.LEFT, padx=5)

        # 提示
        ttk.Label(main, text="保存路径: jqr_description/gestures/*.json",
                  font=('Arial', 8), foreground='gray').pack(pady=3)

    def record(self, key, name):
        """记录当前关节角度"""
        with self.lock:
            if not self.current_positions:
                messagebox.showwarning("无数据", "尚未收到关节状态数据！\n请确保 joint_state_publisher_gui 正在运行。")
                return
            positions = [self.current_positions.get(jn, 0.0) for jn in JOINT_ORDER]
            self.recorded[key] = positions

        # 更新按钮颜色
        self.rec_buttons[key].config(bg='#90ee90')
        self._update_status()
        print(f"✅ 已记录 [{name}]: {[f'{v:.3f}' for v in positions]}")

    def clear(self):
        self.recorded = {}
        for btn in self.rec_buttons.values():
            btn.config(bg='#e8e8e8')
        self._update_status()
        print("已清空所有记录")

    def save_all(self):
        if not self.recorded:
            messagebox.showwarning("无记录", "请先点击按钮录制手势！")
            return

        # 找到 gestures 目录
        script_dir = os.path.dirname(os.path.abspath(__file__))
        gestures_dir = os.path.join(os.path.dirname(script_dir), 'gestures')
        os.makedirs(gestures_dir, exist_ok=True)

        saved = []
        for key, name, fname in GESTURES:
            if key not in self.recorded:
                continue
            positions = self.recorded[key]
            data = {
                'name': name,
                'description': f'{name}手势',
                'joint_names': JOINT_ORDER,
                'trajectory': [
                    {'time': 0.0, 'positions': [0.0] * 13},
                    {'time': 2.0, 'positions': positions},
                    {'time': 4.0, 'positions': positions},
                    {'time': 6.0, 'positions': [0.0] * 13},
                ]
            }
            path = os.path.join(gestures_dir, f'{fname}.json')
            with open(path, 'w') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            saved.append(f'{fname}.json')
            print(f"💾 已保存: {fname}.json ({name})")

        messagebox.showinfo("保存完成",
            f"已保存 {len(saved)} 个手势到:\n{gestures_dir}\n\n{saved}")

    def test_gesture(self):
        """发送最后录制的个手势到控制器测试"""
        if not self.recorded:
            messagebox.showwarning("无记录", "请先录制至少一个手势")
            return

        # 取最后录制的
        last_key = list(self.recorded.keys())[-1]
        positions = self.recorded[last_key]

        traj = JointTrajectory()
        traj.joint_names = JOINT_ORDER
        pt = JointTrajectoryPoint()
        pt.positions = [float(p) for p in positions]
        pt.time_from_start = Duration(sec=2, nanosec=0)
        traj.points.append(pt)

        goal = FollowJointTrajectory.Goal()
        goal.trajectory = traj

        if self.ros_node:
            self.ros_node.send_goal(goal)

    def _update_display(self):
        with self.lock:
            for jn, val in self.joint_labels.items():
                pos = self.current_positions.get(jn, None)
                if pos is not None:
                    val.config(text=f"{pos:+.3f}")
                else:
                    val.config(text=" ---")
        self.root.after(200, self._update_display)

    def _update_status(self):
        if not self.recorded:
            self.status_label.config(text="已录: (无)", foreground='gray')
        else:
            names = [f"{name}" for key, name, _ in GESTURES if key in self.recorded]
            self.status_label.config(
                text=f"已录: {', '.join(names)}", foreground='green')

    def update_positions(self, msg: JointState):
        with self.lock:
            for name, pos in zip(msg.name, msg.position):
                self.current_positions[name] = pos

    def run(self):
        self.root.mainloop()
        if self.ros_node:
            self.ros_node.destroy_node()
        rclpy.shutdown()


class RecorderNode(Node):
    def __init__(self, recorder: GestureRecorder):
        super().__init__('gesture_recorder_node')
        self.recorder = recorder
        self.sub = self.create_subscription(
            JointState, '/joint_states', self._js_callback, 10)
        self._action_client = ActionClient(
            self, FollowJointTrajectory,
            '/joint_trajectory_controller/follow_joint_trajectory')
        self.get_logger().info('手势录制器已启动，等待关节状态...')

    def _js_callback(self, msg):
        self.recorder.update_positions(msg)

    def send_goal(self, goal):
        if not self._action_client.wait_for_server(timeout_sec=2.0):
            self.get_logger().error('无法连接控制器 Action Server')
            return
        future = self._action_client.send_goal_async(goal)
        self.get_logger().info('已发送测试轨迹')


def main():
    app = GestureRecorder()
    app.run()


if __name__ == '__main__':
    main()

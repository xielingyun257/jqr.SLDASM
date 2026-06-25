#!/usr/bin/env python3
"""jqr 手势录制器 — 轻量版，拖滑块→点按钮→保存"""

import os, json, sys, time

# 先试导入 tkinter
try:
    import tkinter as tk
    from tkinter import ttk, messagebox
except Exception as e:
    print(f"无法加载 tkinter: {e}")
    print("请确保在图形界面终端中运行")
    sys.exit(1)

JOINTS = ['joint_1','joint_l_2','joint_l_3','joint_l_4','joint_l_5','joint_l_6','joint_l_7',
          'joint_r_2','joint_r_3','joint_r_4','joint_r_5','joint_r_6','joint_r_7']

GESTURES = [
    ('1','停止','stop', False),
    ('2','直行','go_straight', False),
    ('3','左转弯','left_turn', True),
    ('4','右转弯','right_turn', True),
    ('5','减速慢行','slow_down', False),
    ('6','靠边停车','pull_over', True),
    ('7','变道','lane_change', True),
    ('8','待转','wait_turn', False),
]

# 全局：从 ROS2 回调更新的最新关节值
latest_positions = {}
latest_names = []


def ros_spin_in_thread():
    """在后台线程运行 ROS2 spin，更新 latest_positions"""
    global latest_positions, latest_names
    import rclpy
    from rclpy.node import Node
    from sensor_msgs.msg import JointState

    class Sub(Node):
        def __init__(self):
            super().__init__('_recorder_sub')
            self.sub = self.create_subscription(JointState, '/joint_states', self.cb, 10)
        def cb(self, msg):
            global latest_positions, latest_names
            latest_names = list(msg.name)
            latest_positions = dict(zip(msg.name, msg.position))

    rclpy.init()
    node = Sub()
    try:
        rclpy.spin(node)
    except:
        pass


def main():
    global latest_positions

    # 启动 ROS2 后台线程
    import threading
    t = threading.Thread(target=ros_spin_in_thread, daemon=True)
    t.start()
    time.sleep(1.0)  # 等订阅建立

    # ---- GUI ----
    root = tk.Tk()
    root.title("jqr 手势录制器")
    root.geometry("580x500")
    root.resizable(False, False)

    recorded = {}

    # 关节显示标签
    joint_labels = {}
    main_frame = ttk.Frame(root, padding=8)
    main_frame.pack(fill=tk.BOTH, expand=True)

    ttk.Label(main_frame, text="jqr 手势录制器", font=('Arial', 14, 'bold')).pack()
    ttk.Label(main_frame, text="①拖滑块→②点「读取」→③点手势按钮→④保存",
              font=('Arial', 9)).pack(pady=2)

    f = ttk.LabelFrame(main_frame, text="当前关节值", padding=4)
    f.pack(fill=tk.X, pady=3)
    for i, jn in enumerate(JOINTS):
        r, c = i // 2, (i % 2) * 2
        ttk.Label(f, text=f"{jn}:", width=10, anchor=tk.E).grid(row=r, column=c, sticky=tk.E, padx=1)
        v = ttk.Label(f, text=" ---", width=7, anchor=tk.W, font=('Courier', 9))
        v.grid(row=r, column=c+1, sticky=tk.W, padx=1)
        joint_labels[jn] = v

    def refresh():
        """更新显示"""
        for jn in JOINTS:
            if jn in latest_positions:
                joint_labels[jn].config(text=f"{latest_positions[jn]:+.3f}")
            else:
                joint_labels[jn].config(text=" ---")
        root.after(300, refresh)

    def record(key, name):
        pos = [latest_positions.get(jn, 0.0) for jn in JOINTS]
        recorded[key] = pos
        buttons[key].config(bg='#90ee90')
        status.config(text=f"已录: {' '.join(k for k in recorded)}", foreground='green')
        print(f"[{name}] {[f'{v:.3f}' for v in pos]}")

    def clear():
        recorded.clear()
        for b in buttons.values():
            b.config(bg='#e8e8e8')
        status.config(text="已录: (无)", foreground='gray')

    def save():
        if not recorded:
            messagebox.showwarning("提示", "请先录制手势")
            return
        d = os.path.dirname(os.path.abspath(__file__))
        gd = os.path.join(os.path.dirname(d), 'gestures')
        os.makedirs(gd, exist_ok=True)
        for key, name, fname, swing in GESTURES:
            if key not in recorded:
                continue
            p = [float(v) for v in recorded[key]]
            pts = [{'time':0.0, 'positions':[0.0]*13}]
            if swing:
                # 来回摆动：开始位→原位→开始位→原位 (2个来回)
                for cyc in range(2):
                    pts.append({'time': 1.0+cyc*2.0, 'positions': p})
                    pts.append({'time': 2.0+cyc*2.0, 'positions': [0.0]*13})
            else:
                pts.append({'time': 2.0, 'positions': p})
                pts.append({'time': 4.0, 'positions': p})
                pts.append({'time': 6.0, 'positions': [0.0]*13})
            data = {'name': name, 'description': f'{name}手势',
                    'joint_names': JOINTS, 'trajectory': pts}
            with open(os.path.join(gd, f'{fname}.json'), 'w') as fp:
                json.dump(data, fp, indent=2, ensure_ascii=False)
        messagebox.showinfo("完成", f"已保存 {len(recorded)} 个手势")

    def test():
        if not recorded:
            messagebox.showwarning("提示", "请先录制手势")
            return
        k = list(recorded.keys())[-1]
        p = ','.join(str(v) for v in recorded[k])
        j = ','.join(JOINTS)
        cmd = (f'ros2 action send_goal /joint_trajectory_controller/follow_joint_trajectory '
               f'control_msgs/action/FollowJointTrajectory '
               f'"{{trajectory: {{joint_names: [{j}], points: [{{positions: [{p}], time_from_start: {{sec:2, nanosec:0}}}}]}}}}"')
        os.system(cmd + ' 2>&1 | grep -E "SUCCEEDED|Goal"')

    ttk.Button(main_frame, text="🔄 读取当前关节角度",
               command=refresh).pack(pady=4)

    bf = ttk.LabelFrame(main_frame, text="手势按钮", padding=6)
    bf.pack(fill=tk.X, pady=3)
    buttons = {}
    for i, (key, name, fname, swing) in enumerate(GESTURES):
        r, c = i // 4, i % 4
        lbl = f"{key}. {name}{' ↕' if swing else ''}"
        btn = tk.Button(bf, text=lbl, width=14, height=2, bg='#e8e8e8', font=('Arial', 9, 'bold'),
                       command=lambda k=key, n=name: record(k, n))
        btn.grid(row=r, column=c, padx=3, pady=2)
        buttons[key] = btn

    status = ttk.Label(main_frame, text="已录: (无)", font=('Arial', 10), foreground='gray')
    status.pack(pady=3)

    bf2 = ttk.Frame(main_frame)
    bf2.pack(pady=5)
    tk.Button(bf2, text="清空", bg='#ffaaaa', width=10, command=clear).pack(side=tk.LEFT, padx=4)
    tk.Button(bf2, text="保存全部", bg='#aaffaa', width=10, command=save).pack(side=tk.LEFT, padx=4)
    tk.Button(bf2, text="测试", bg='#aaaaff', width=10, command=test).pack(side=tk.LEFT, padx=4)
    ttk.Label(main_frame, text="保存到: jqr_description/gestures/*.json",
              font=('Arial', 7), foreground='gray').pack(pady=2)
    ttk.Label(main_frame, text="↕ = 含来回摆动(记录起始位即可)",
              font=('Arial', 7), foreground='#666').pack()

    root.after(300, refresh)
    root.mainloop()


if __name__ == '__main__':
    main()

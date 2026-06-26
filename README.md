# jqr.SLDASM — 交通指挥手势机器人

双机械臂人形上半身机器人，用于交通指挥手势演示。基于 ROS2 Humble + RViz2，不依赖 Gazebo。

## 目录结构

```
jqr.SLDASM/
├── README.md
├── scripts/jqr_description/          # ROS2 功能包
│   ├── launch/
│   │   ├── controller_rviz.launch.py  # 控制器模式（滑块拖动关节）
│   │   ├── gesture_rviz.launch.py     # 手势模式（循环播放8种手势）
│   │   ├── display.launch.py          # 参考：原始滑块演示
│   │   ├── demo.launch.py             # 参考：RViz 可视化
│   │   └── rviz_gesture.launch.py     # 参考：另一手势启动变体
│   ├── scripts/
│   │   ├── start_gesture_rviz.sh      # ★ 手势模式一键启动
│   │   ├── start_controller_rviz.sh   # ★ 控制器模式一键启动
│   │   ├── gesture_publisher.py       # 手势循环发布器（50Hz）
│   │   ├── gesture_player.py          # 手势播放器（终端交互）
│   │   ├── gesture_recorder.py        # 手势录制工具
│   │   ├── robot_description_publisher.py  # URDF 发布器
│   │   └── zero_joint_publisher.py    # 零位关节发布器
│   ├── config/
│   │   └── controllers.yaml           # 控制器参数（参考）
│   ├── gestures/                      # 8 种交通指挥手势 JSON
│   ├── urdf/jqr.SLDASM.urdf           # 机器人 URDF 模型
│   ├── rviz/display.rviz              # RViz2 显示配置
│   └── meshes/                        # 3D 网格文件（.STL）
```

## 快速开始

### 环境要求

- Ubuntu 22.04
- ROS2 Humble
- 依赖包：`ros-humble-robot-state-publisher`、`ros-humble-joint-state-publisher-gui`、`ros-humble-rviz2`

### 构建

```bash
cd jqr.SLDASM
colcon build --packages-select jqr_description
source install/setup.bash
```

### 运行

**手势模式** — 循环播放 8 种交通指挥手势：
```bash
bash scripts/jqr_description/scripts/start_gesture_rviz.sh
```

**控制器模式** — RViz2 滑块拖动控制每个关节：
```bash
bash scripts/jqr_description/scripts/start_controller_rviz.sh
```

`Ctrl+C` 停止。

## 两种模式

| | 手势模式 | 控制器模式 |
|---|---|---|
| `/joint_states` 发布者 | `gesture_publisher.py`（轨迹播放） | `joint_state_publisher_gui`（滑块） |
| 手势播放 | ✅ 8 种手势循环 | — |
| 手动控制 | — | ✅ 拖动滑块 |
| ros2_control | 不需要 | 不需要 |
| Gazebo | 不需要 | 不需要 |

两种模式完全独立，互不干扰。

## 手势文件

`gestures/` 目录下 8 个 JSON 文件对应 8 种交通指挥手势：

| 编号 | 手势 | 文件 |
|------|------|------|
| 1 | 停止 | `stop.json` |
| 2 | 直行 | `go_straight.json` |
| 3 | 左转弯 | `left_turn.json` |
| 4 | 右转弯 | `right_turn.json` |
| 5 | 减速慢行 | `slow_down.json` |
| 6 | 靠边停车 | `pull_over.json` |
| 7 | 变道 | `lane_change.json` |
| 8 | 待转 | `wait_turn.json` |

每个手势包含 13 个关节的时间序列轨迹，50Hz 插值播放。

## 运动链

```
base_link（基座）
  └── joint_1（腰部 Z 旋转）→ link_1（躯干）
       ├── joint_l_2（左肩 X）→ joint_l_3（Y）→ joint_l_4（Z）
       │    → joint_l_5（左肘 X）→ joint_l_6（Z）→ joint_l_7（左手 X）
       └── joint_r_2（右肩 X）→ joint_r_3（Y）→ joint_r_4（Z）
            → joint_r_5（右肘 X）→ joint_r_6（Z）→ joint_r_7（右手 X）
```

## 许可

BSD

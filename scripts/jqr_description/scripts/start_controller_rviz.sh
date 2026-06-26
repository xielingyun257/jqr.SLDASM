#!/bin/bash
# ╔══════════════════════════════════════╗
# ║  jqr 控制器模式 — RViz2             ║
# ║  无 Gazebo，有控制器                ║
# ║  ros2_control + trajectory_ctrl     ║
# ╚══════════════════════════════════════╝
set -e
SCRIPT_DIR=$(dirname "$(realpath "$0")")
WS_DIR=$(dirname "$(dirname "$(dirname "$SCRIPT_DIR")")")
source /opt/ros/humble/setup.bash
source "$WS_DIR/install/setup.bash"

echo ">>> 清理..."
for p in rviz2 robot_state_publisher controller_manager; do
    killall -9 $p 2>/dev/null || true
done
sleep 1

echo ">>> 启动控制器模式..."
ros2 launch jqr_description controller_rviz.launch.py 2>&1 &
LAUNCH_PID=$!

echo ""
echo "╔════════════════════════════╗"
echo "║  控制器模式 - RViz2       ║"
echo "║  gesture_player 终端交互  ║"
echo "║  Ctrl+C 停止              ║"
echo "╚════════════════════════════╝"

wait $LAUNCH_PID

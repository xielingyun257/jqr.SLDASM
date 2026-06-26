#!/bin/bash
# ╔══════════════════════════════════════╗
# ║  jqr 控制器模式 — RViz2 滑块拖动   ║
# ║  无 Gazebo，无 ros2_control        ║
# ║  joint_state_publisher_gui → 滑块  ║
# ╚══════════════════════════════════════╝
SCRIPT_DIR=$(dirname "$(realpath "$0")")
WS_DIR=$(dirname "$(dirname "$(dirname "$SCRIPT_DIR")")")
source /opt/ros/humble/setup.bash
source "$WS_DIR/install/setup.bash"

echo ">>> 清理..."
for p in rviz2 robot_state_publisher joint_state_publisher_gui controller_manager; do
    killall -9 $p 2>/dev/null || true
done
pkill -9 -f "jqr_description" 2>/dev/null || true
sleep 1
ros2 daemon stop 2>/dev/null || true
ros2 daemon start 2>/dev/null || true
sleep 1

echo ">>> 启动控制器模式（RViz2 滑块拖动关节控制）..."
ros2 launch jqr_description controller_rviz.launch.py 2>&1

echo ""
echo "╔══════════════════════════════════════╗"
echo "║  控制器模式 - RViz2 滑块拖动        ║"
echo "║  拖动滑块控制关节角度               ║"
echo "║  Ctrl+C 停止                        ║"
echo "╚══════════════════════════════════════╝"

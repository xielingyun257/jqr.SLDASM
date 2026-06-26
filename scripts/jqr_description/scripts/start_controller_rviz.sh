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
for p in rviz2 robot_state_publisher controller_manager joint_state_publisher_gui; do
    killall -9 $p 2>/dev/null || true
done
# 用安装路径精确杀孤儿 Python 节点（避免误杀本 bash 进程）
LIB_DIR="$WS_DIR/install/jqr_description/lib/jqr_description"
pkill -9 -f "$LIB_DIR/gesture_publisher" 2>/dev/null || :
pkill -9 -f "$LIB_DIR/gesture_player" 2>/dev/null || :
pkill -9 -f "$LIB_DIR/robot_description_publisher" 2>/dev/null || :
pkill -9 -f "$LIB_DIR/zero_joint_publisher" 2>/dev/null || :
sleep 1

echo ">>> 启动控制器模式（RViz2 滑块拖动关节控制）..."
ros2 launch jqr_description controller_rviz.launch.py 2>&1

echo ""
echo "╔══════════════════════════════════════╗"
echo "║  控制器模式 - RViz2 滑块拖动        ║"
echo "║  拖动滑块控制关节角度               ║"
echo "║  Ctrl+C 停止                        ║"
echo "╚══════════════════════════════════════╝"

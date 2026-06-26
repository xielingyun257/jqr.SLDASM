#!/bin/bash
# ╔══════════════════════════════════════╗
# ║  jqr 手势演示 — RViz2 模式          ║
# ║  无 Gazebo，无控制器                ║
# ║  gesture_publisher → /joint_states  ║
# ╚══════════════════════════════════════╝
SCRIPT_DIR=$(dirname "$(realpath "$0")")
WS_DIR=$(dirname "$(dirname "$(dirname "$SCRIPT_DIR")")")
source /opt/ros/humble/setup.bash
source "$WS_DIR/install/setup.bash"

echo ">>> 清理..."
# 清理残留进程
for p in rviz2 robot_state_publisher controller_manager joint_state_publisher_gui; do
    killall -9 $p 2>/dev/null || true
done
# 清理 ros2 launch 遗留的孤儿节点（多 publisher 会导致闪回零位）
pkill -9 -f "jqr_description" 2>/dev/null; true
sleep 1
# 重建 ROS2 图
ros2 daemon stop 2>/dev/null; true
ros2 daemon start 2>/dev/null; true
sleep 1

echo ">>> [1/2] 启动手势发布器（先占 /joint_states，供 RSP 初始化）..."
ros2 run jqr_description gesture_publisher.py 2>&1 &
GESTURE_PID=$!
sleep 3

echo ">>> [2/2] 启动 RViz2 + TF..."
ros2 launch jqr_description gesture_rviz.launch.py 2>&1 &
RVIZ_PID=$!
sleep 5

echo ""
echo "╔══════════════════════════╗"
echo "║  手势演示 - RViz2 模式  ║"
echo "║  Ctrl+C 停止            ║"
echo "╚══════════════════════════╝"

wait $GESTURE_PID
kill $RVIZ_PID 2>/dev/null || true
wait

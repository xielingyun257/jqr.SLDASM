#!/bin/bash
# ╔══════════════════════════════════════════╗
# ║  jqr 交通指挥手势 — 全仿真一键启动      ║
# ║  Gazebo + RViz2 + 8 手势               ║
# ╚══════════════════════════════════════════╝
set -e

SCRIPT_DIR=$(dirname "$(realpath "$0")")
WS_DIR=$(dirname "$(dirname "$(dirname "$SCRIPT_DIR")")")
source /opt/ros/humble/setup.bash
source "$WS_DIR/install/setup.bash"

# ═══ 清理 ═══
echo ">>> 清理残余进程..."
for p in gzserver gzclient gz_sim ruby rviz2 robot_state_publisher joint_state_publisher controller_manager; do
    killall -9 $p 2>/dev/null || true
done
sleep 1
echo "  ✅ 清理完毕"

WORLD=$WS_DIR/install/jqr_description/share/jqr_description/worlds/traffic_world.sdf
SDF=/tmp/jqr_controlled.sdf

# ═══ 0. 生成固定 SDF ═══
echo ">>> [0/6] 生成固定底座 SDF..."
python3 "$WS_DIR/install/jqr_description/lib/jqr_description/gen_fixed_sdf.py" 2>&1
echo "  ✅ SDF 就绪"

# ═══ 1. Gazebo ═══
echo ">>> [1/6] 启动 Gazebo..."
ign gazebo "$WORLD" -r 2>/dev/null &
sleep 8
echo "  ✅ Gazebo 就绪"

# ═══ 2. 机器人 ═══
echo ">>> [2/6] 生成机器人 (z=1.06, 脚底贴站台)..."
ros2 run ros_gz_sim create -file "$SDF" -name jqr -x 0 -y 0 -z 1.06 2>&1
sleep 3
echo "  ✅ 机器人已放置"

# ═══ 3. 桥接 ═══
echo ">>> [3/6] 启动 Gazebo 桥接..."
ros2 run jqr_description gz_joint_bridge.py 2>&1 &
BRIDGE_PID=$!
sleep 2
echo "  ✅ 桥接就绪 (PID=$BRIDGE_PID)"

# ═══ 4. 手势（前置启动，确保RViz2有TF数据）═══
echo ">>> [4/6] 启动手势发布器（零位初始化）..."
ros2 run jqr_description gesture_publisher.py 2>&1 &
GESTURE_PID=$!
# 等待零位初始化完成 (gesture_publisher 前2秒发布零位)
sleep 3
echo "  ✅ 零位就绪，关节状态已发布 (PID=$GESTURE_PID)"

# ═══ 5. RViz2 + TF（此时 /joint_states 已有数据）═══
echo ">>> [5/6] 启动 RViz2 + TF..."
ros2 launch jqr_description demo.launch.py 2>&1 &
RVIZ_PID=$!
sleep 6
echo "  ✅ RViz2 就绪 (PID=$RVIZ_PID)"

# ═══ 6. 等待手势演示完成 ═══
echo ">>> [6/6] 手势演示进行中..."
echo "     (Gazebo 与 RViz2 已同步运行)"
wait $GESTURE_PID

echo ""
echo "╔══════════════════════════════════════╗"
echo "║  ✅ 全仿真演示完毕                   ║"
echo "╚══════════════════════════════════════╝"

# 清理后台进程
kill $BRIDGE_PID $RVIZ_PID 2>/dev/null || true
wait

#!/bin/bash
# ╔══════════════════════════════════════════╗
# ║  jqr 手势演示 — 新架构一键启动          ║
# ║  Gazebo (JointTrajectoryController)      ║
# ║  + RViz2 (无控制器干扰)                 ║
# ╚══════════════════════════════════════════╝
set -e

SCRIPT_DIR=$(dirname "$(realpath "$0")")
WS_DIR=$(dirname "$(dirname "$(dirname "$SCRIPT_DIR")")")
source /opt/ros/humble/setup.bash
source "$WS_DIR/install/setup.bash"

# ═══ 清理 ═══
echo ">>> 清理残余进程..."
for p in gzserver gzclient gz_sim ruby rviz2 robot_state_publisher controller_manager; do
    killall -9 $p 2>/dev/null || true
done
sleep 1
echo "  ✅ 清理完毕"

# ═══ 0. 生成 SDF ═══
echo ">>> [0/4] 生成 SDF (JointTrajectoryController)..."
python3 "$SCRIPT_DIR/gen_sdf_traj.py"
echo "  ✅ SDF 就绪"

WORLD=$WS_DIR/install/jqr_description/share/jqr_description/worlds/traffic_world.sdf

# ═══ 1. Gazebo ═══
echo ">>> [1/4] 启动 Gazebo..."
export MESA_GL_VERSION_OVERRIDE=3.3
ign gazebo "$WORLD" -r 2>/dev/null &
sleep 8
echo "  ✅ Gazebo 就绪"

# ═══ 2. 机器人 ═══
echo ">>> [2/4] 生成机器人 (z=1.63)..."
ros2 run ros_gz_sim create -file /tmp/jqr_controlled.sdf -name jqr -x 0 -y 0 -z 1.63
sleep 2
echo "  ✅ 机器人已放置"

# ═══ 3. 手势演示（统一驱动 Gazebo + RViz2）═══
echo ">>> [3/4] 启动手势演示..."
python3 "$SCRIPT_DIR/gesture_demo.py" 2>&1 &
GESTURE_PID=$!
sleep 4  # 等待零位初始化
echo "  ✅ 手势演示就绪 (PID=$GESTURE_PID)"

# ═══ 4. RViz2 + TF ═══
echo ">>> [4/4] 启动 RViz2 + TF..."
ros2 launch "$SCRIPT_DIR/../launch/gesture_rviz.launch.py" 2>&1 &
RVIZ_PID=$!
sleep 6
echo "  ✅ RViz2 就绪 (PID=$RVIZ_PID)"

echo ""
echo "╔══════════════════════════════════════╗"
echo "║  手势演示运行中                      ║"
echo "║  Gazebo: JointTrajectoryController   ║"
echo "║  RViz2:  /joint_states → TF          ║"
echo "║  Ctrl+C 停止                         ║"
echo "╚══════════════════════════════════════╝"

# 等待手势演示完成或被中断
wait $GESTURE_PID

# 清理
kill $RVIZ_PID 2>/dev/null || true
wait

#!/usr/bin/env python3
"""
jqr 交通指挥手势 - Ignition Gazebo 完整启动文件

启动组件：
  1. Ignition Gazebo + 交通世界（马路、车辆、站台）
  2. ros2_control_node + joint_trajectory_controller + joint_state_broadcaster
  3. 在 Gazebo 中生成机器人模型
  4. robot_state_publisher（TF）
  5. RViz2（可视化）
  6. gesture_player（手势播放器，终端交互）

用法：
  ros2 launch jqr_description traffic_gesture.launch.py
  ros2 launch jqr_description traffic_gesture.launch.py world_file:=/path/to/world.sdf
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument, ExecuteProcess, RegisterEventHandler,
    TimerAction, LogInfo
)
from launch.event_handlers import OnProcessExit
from launch.substitutions import LaunchConfiguration, Command
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    pkg_dir = get_package_share_directory('jqr_description')

    # 文件路径
    world_file = os.path.join(pkg_dir, 'worlds', 'traffic_world.sdf')
    urdf_file = os.path.join(pkg_dir, 'urdf', 'jqr.SLDASM.urdf')
    rviz_file = os.path.join(pkg_dir, 'rviz', 'display.rviz')
    controllers_file = os.path.join(pkg_dir, 'config', 'controllers.yaml')

    with open(urdf_file, 'r') as f:
        robot_desc = f.read()

    robot_desc_param = {'robot_description': robot_desc}

    return LaunchDescription([
        # === 参数声明 ===
        DeclareLaunchArgument(
            'world_file', default_value=world_file,
            description='Gazebo 世界 SDF 文件路径'
        ),

        # ============================================================
        # 1. Ignition Gazebo 仿真器
        # ============================================================
        ExecuteProcess(
            cmd=['ign', 'gazebo', world_file, '-r'],
            output='screen',
            name='ign_gazebo',
        ),

        # 等待 Gazebo 启动后生成模型
        TimerAction(
            period=3.0,
            actions=[
                ExecuteProcess(
                    cmd=[
                        'ros2', 'run', 'ros_gz_sim', 'create',
                        '-file', urdf_file,
                        '-name', 'jqr',
                        '-x', '0.0', '-y', '0.0', '-z', '0.35',
                    ],
                    output='screen',
                    name='spawn_robot',
                ),
            ],
        ),

        # ============================================================
        # 2. ros2_control 控制节点
        # ============================================================
        Node(
            package='controller_manager',
            executable='ros2_control_node',
            name='controller_manager',
            output='screen',
            parameters=[controllers_file, robot_desc_param],
        ),

        # 加载 joint_state_broadcaster
        TimerAction(
            period=5.0,
            actions=[
                ExecuteProcess(
                    cmd=[
                        'ros2', 'run', 'controller_manager', 'spawner',
                        'joint_state_broadcaster',
                    ],
                    output='screen',
                    name='spawn_broadcaster',
                ),
            ],
        ),

        # 加载 joint_trajectory_controller
        TimerAction(
            period=6.0,
            actions=[
                ExecuteProcess(
                    cmd=[
                        'ros2', 'run', 'controller_manager', 'spawner',
                        'joint_trajectory_controller',
                        '-c', '/controller_manager',
                    ],
                    output='screen',
                    name='spawn_controller',
                ),
            ],
        ),

        # ============================================================
        # 3. 将 robot_description 发布到 /rviz_robot_description（RViz2 需要）
        # ============================================================
        Node(
            package='jqr_description',
            executable='robot_description_publisher.py',
            name='robot_description_publisher',
            output='screen',
            parameters=[robot_desc_param],
        ),

        # ============================================================
        # 4. robot_state_publisher (TF)
        # ============================================================
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            output='screen',
            parameters=[robot_desc_param],
        ),

        # ============================================================
        # 5. RViz2 可视化
        # ============================================================
        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            output='screen',
            arguments=['-d', rviz_file],
        ),

        # ============================================================
        # 6. 手势播放器（终端交互）
        # ============================================================
        TimerAction(
            period=8.0,
            actions=[
                ExecuteProcess(
                    cmd=[
                        'ros2', 'run', 'jqr_description', 'gesture_player.py',
                    ],
                    output='screen',
                    name='gesture_player',
                    prefix='x-terminal-emulator -e',  # 在新终端中运行
                ),
            ],
        ),

        LogInfo(msg='jqr 交通指挥手势系统启动中...'),
    ])

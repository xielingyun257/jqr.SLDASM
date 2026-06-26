#!/usr/bin/env python3
"""
jqr 控制器模式 — 纯 RViz2（无 Gazebo）

基于 traffic_gesture.launch.py，移除 Gazebo 相关组件：
  - 1. ros2_control_node + joint_trajectory_controller + joint_state_broadcaster
  - 2. robot_state_publisher（TF）
  - 3. RViz2（可视化）
  - 4. gesture_player（终端交互）

用法：
  ros2 launch jqr_description controller_rviz.launch.py
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import ExecuteProcess, TimerAction, LogInfo
from launch_ros.actions import Node


def generate_launch_description():
    pkg_dir = get_package_share_directory('jqr_description')

    urdf_file = os.path.join(pkg_dir, 'urdf', 'jqr.SLDASM.urdf')
    rviz_file = os.path.join(pkg_dir, 'rviz', 'display.rviz')
    controllers_file = os.path.join(pkg_dir, 'config', 'controllers.yaml')

    with open(urdf_file, 'r') as f:
        robot_desc = f.read()

    robot_desc_param = {'robot_description': robot_desc}

    return LaunchDescription([
        # ============================================================
        # 1. ros2_control 控制节点
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
            period=3.0,
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
            period=4.0,
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
        # 2. robot_description_publisher（RViz2 需要独立 topic）
        # ============================================================
        Node(
            package='jqr_description',
            executable='robot_description_publisher.py',
            name='robot_description_publisher',
            output='screen',
            parameters=[robot_desc_param],
        ),

        # ============================================================
        # 3. robot_state_publisher (TF)
        # ============================================================
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            output='screen',
            parameters=[robot_desc_param],
        ),

        # ============================================================
        # 4. RViz2 可视化
        # ============================================================
        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            output='screen',
            arguments=['-d', rviz_file],
        ),

        # ============================================================
        # 5. gesture_player（终端交互 - FollowJointTrajectory action）
        # ============================================================
        TimerAction(
            period=6.0,
            actions=[
                ExecuteProcess(
                    cmd=[
                        'ros2', 'run', 'jqr_description', 'gesture_player.py',
                    ],
                    output='screen',
                    name='gesture_player',
                ),
            ],
        ),

        LogInfo(msg='jqr 控制器模式 — 纯 RViz2（无 Gazebo）启动中...'),
    ])

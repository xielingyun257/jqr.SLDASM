#!/usr/bin/env python3
"""
jqr 手势演示 RViz 启动文件（RViz2 可视化 + TF 树）

启动组件：
  - robot_state_publisher：从参数读取 URDF，监听 /joint_states → 发布 TF
  - joint_state_publisher：发布默认零位关节状态（无 GUI，不争抢话题）
  - robot_description_publisher：发布 /rviz_robot_description（供 RViz2）
  - rviz2：3D 可视化（延迟启动，等待发布器就绪）

⚠ 不使用 joint_state_publisher_gui，以免与手势播放器争抢 /joint_states
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import TimerAction
from launch_ros.actions import Node


def generate_launch_description():
    pkg_dir = get_package_share_directory('jqr_description')

    urdf_file = os.path.join(pkg_dir, 'urdf', 'jqr.SLDASM.urdf')
    rviz_file = os.path.join(pkg_dir, 'rviz', 'display.rviz')

    with open(urdf_file, 'r') as f:
        robot_desc = f.read()

    robot_desc_param = {'robot_description': robot_desc}

    return LaunchDescription([
        # TF 树（从 /joint_states 读取关节值）
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            output='screen',
            parameters=[robot_desc_param],
        ),

        # 默认零位关节状态（独立发布到 /joint_states）
        Node(
            package='jqr_description',
            executable='zero_joint_publisher.py',
            name='zero_joint_publisher',
            output='screen',
        ),

        # 将 URDF 发布到 /robot_description（joint_state_publisher 需要）
        # 同时发布到 /rviz_robot_description（RViz2 需要，独立话题避免冲突）
        Node(
            package='jqr_description',
            executable='robot_description_publisher.py',
            name='robot_description_publisher',
            output='screen',
            parameters=[robot_desc_param],
        ),

        # RViz2 延迟 2 秒启动，确保 /joint_states 和 /rviz_robot_description 已就绪
        TimerAction(
            period=2.0,
            actions=[
                Node(
                    package='rviz2',
                    executable='rviz2',
                    name='rviz2',
                    output='screen',
                    arguments=['-d', rviz_file],
                ),
            ],
        ),
    ])

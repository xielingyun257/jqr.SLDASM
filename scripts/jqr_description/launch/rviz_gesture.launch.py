#!/usr/bin/env python3
"""
jqr RViz2 手势演示启动文件（仅 RViz，不含 Gazebo）

启动组件：
  - robot_state_publisher：监听 /joint_states → 发布 TF
  - robot_description_publisher：发布 URDF 到 /rviz_robot_description
  - rviz2：3D 可视化（延迟 2s 等待发布器就绪）
  - gesture_publisher：8 种交通指挥手势循环演示

⚠ 不启动 joint_state_publisher / zero_joint_publisher，由 gesture_publisher 独占 /joint_states
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
        # TF 树（监听 /joint_states）
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            output='screen',
            parameters=[robot_desc_param],
        ),

        # 发布 URDF（/robot_description + /rviz_robot_description）
        Node(
            package='jqr_description',
            executable='robot_description_publisher.py',
            name='robot_description_publisher',
            output='screen',
            parameters=[robot_desc_param],
        ),

        # RViz2 延迟 2s 启动
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

        # 手势发布器（延迟 4s，确保 RViz2 就绪后再开始播放）
        TimerAction(
            period=4.0,
            actions=[
                Node(
                    package='jqr_description',
                    executable='gesture_publisher.py',
                    name='gesture_player',
                    output='screen',
                ),
            ],
        ),
    ])

#!/usr/bin/env python3
"""
jqr 双机械臂 RViz 可视化启动文件

启动组件：
  - robot_state_publisher：发布 TF 变换树（从参数读取 URDF）
  - robot_description_publisher：将 URDF 发布到 /rviz_robot_description（供 RViz2）
  - joint_state_publisher_gui：GUI 滑块控制关节角度（从参数读取 URDF）
  - rviz2：3D 可视化（从 /rviz_robot_description topic 加载 URDF）

设计要点：
  - /rviz_robot_description 是独立话题，与 GUI 监听的 /robot_description 隔离
  - GUI 只从参数获取 URDF，/robot_description 上无消息，不会触发重置
  - /rviz_robot_description 上可安全重发，不影响 GUI

用法：
  ros2 launch jqr_description display.launch.py
"""

import os
from ament_index_python.packages import get_package_share_directory, get_package_prefix
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch_ros.actions import Node


def generate_launch_description():
    pkg_dir = get_package_share_directory('jqr_description')
    pkg_prefix = get_package_prefix('jqr_description')

    urdf_file = os.path.join(pkg_dir, 'urdf', 'jqr.SLDASM.urdf')
    rviz_file = os.path.join(pkg_dir, 'rviz', 'display.rviz')

    with open(urdf_file, 'r') as f:
        robot_desc = f.read()

    robot_desc_param = {'robot_description': robot_desc}

    return LaunchDescription([
        DeclareLaunchArgument(
            'model',
            default_value=urdf_file,
            description='URDF 模型文件路径'
        ),

        # 1. robot_state_publisher: 发布 TF 变换
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            output='screen',
            parameters=[robot_desc_param],
        ),

        # 2. 将 URDF 发布到 /rviz_robot_description（独立话题，不影响 GUI）
        Node(
            package='jqr_description',
            executable='robot_description_publisher.py',
            name='robot_description_publisher',
            output='screen',
            parameters=[robot_desc_param],
        ),

        # 3. GUI 关节调试工具（从参数获取 URDF）
        Node(
            package='joint_state_publisher_gui',
            executable='joint_state_publisher_gui',
            name='joint_state_publisher_gui',
            output='screen',
            parameters=[robot_desc_param],
        ),

        # 4. RViz 可视化（从 /rviz_robot_description topic 加载 URDF）
        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            output='screen',
            arguments=['-d', rviz_file],
        ),
    ])

#!/usr/bin/env python3
"""
jqr 控制器模式 — RViz2 滑块拖动关节控制

基于 display.launch.py，纯 RViz2 可视化 + GUI 滑块：
  - 1. robot_state_publisher（TF 变换树）
  - 2. robot_description_publisher（/rviz_robot_description，供 RViz2）
  - 3. joint_state_publisher_gui（GUI 滑块控制关节角度）
  - 4. rviz2（3D 可视化）

⚠ 不含 Gazebo，不含 ros2_control

用法：
  ros2 launch jqr_description controller_rviz.launch.py
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch_ros.actions import Node


def generate_launch_description():
    pkg_dir = get_package_share_directory('jqr_description')

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

        # 3. GUI 关节滑块控制（从参数获取 URDF）
        Node(
            package='joint_state_publisher_gui',
            executable='joint_state_publisher_gui',
            name='joint_state_publisher_gui',
            output='screen',
            parameters=[robot_desc_param],
        ),

        # 4. RViz2 可视化（从 /rviz_robot_description topic 加载 URDF）
        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            output='screen',
            arguments=['-d', rviz_file],
        ),
    ])

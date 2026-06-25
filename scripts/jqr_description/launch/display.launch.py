#!/usr/bin/env python3
"""
jqr 双机械臂 RViz 可视化启动文件

启动组件：
  - robot_state_publisher：发布 TF 变换树
  - joint_state_publisher_gui：GUI 滑块控制关节角度
  - rviz2：3D 可视化

用法：
  ros2 launch jqr_description display.launch.py
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    pkg_dir = get_package_share_directory('jqr_description')

    urdf_file = os.path.join(pkg_dir, 'urdf', 'jqr.SLDASM.urdf')
    rviz_file = os.path.join(pkg_dir, 'rviz', 'display.rviz')

    with open(urdf_file, 'r') as f:
        robot_desc = f.read()

    return LaunchDescription([
        # 可选：通过命令行参数覆盖 URDF 路径
        DeclareLaunchArgument(
            'model',
            default_value=urdf_file,
            description='URDF 模型文件路径'
        ),

        # 将 URDF 加载到参数服务器
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            output='screen',
            parameters=[{'robot_description': robot_desc}],
        ),

        # GUI 关节调试工具
        Node(
            package='joint_state_publisher_gui',
            executable='joint_state_publisher_gui',
            name='joint_state_publisher_gui',
            output='screen',
        ),

        # RViz 可视化
        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            output='screen',
            arguments=['-d', rviz_file],
        ),
    ])

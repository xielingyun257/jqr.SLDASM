#!/usr/bin/env python3
"""
jqr 双机械臂 RViz 可视化启动文件

启动组件：
  - robot_state_publisher：发布 TF 变换树
  - robot_description_publisher：将 URDF 参数转发到话题（供 RViz2 订阅）
  - joint_state_publisher_gui：GUI 滑块控制关节角度
  - rviz2：3D 可视化

用法：
  ros2 launch jqr_description display.launch.py
"""

import os
from ament_index_python.packages import get_package_share_directory, get_package_prefix
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

ROBOT_DESC_PARAM = {'robot_description': None}


def generate_launch_description():
    pkg_dir = get_package_share_directory('jqr_description')
    pkg_prefix = get_package_prefix('jqr_description')

    urdf_file = os.path.join(pkg_dir, 'urdf', 'jqr.SLDASM.urdf')
    rviz_file = os.path.join(pkg_dir, 'rviz', 'display.rviz')

    # 发布脚本路径
    publisher_script = os.path.join(
        pkg_prefix, 'lib', 'jqr_description', 'robot_description_publisher.py'
    )

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

        # 2. 将 robot_description 参数转发到话题（RViz2 需要）
        Node(
            package='jqr_description',
            executable='robot_description_publisher.py',
            name='robot_description_publisher',
            output='screen',
            parameters=[robot_desc_param],
        ),

        # 3. GUI 关节调试工具
        Node(
            package='joint_state_publisher_gui',
            executable='joint_state_publisher_gui',
            name='joint_state_publisher_gui',
            output='screen',
            parameters=[robot_desc_param],
        ),

        # 4. RViz 可视化
        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            output='screen',
            arguments=['-d', rviz_file],
        ),
    ])

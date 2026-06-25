#!/usr/bin/env python3
"""
jqr 双机械臂 Gazebo 仿真启动文件

启动组件：
  - Gazebo 空世界
  - spawn_model：生成机器人模型
  - robot_state_publisher：发布 TF 变换树
  - joint_state_publisher：发布关节状态

用法：
  ros2 launch jqr_description gazebo.launch.py

注意：
  当前为基础版本，仅完成模型生成与可视化。
  后续需要添加 ros2_control 控制器配置才能实现力控/位控仿真。
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node


def generate_launch_description():
    pkg_dir = get_package_share_directory('jqr_description')

    urdf_file = os.path.join(pkg_dir, 'urdf', 'jqr.SLDASM.urdf')

    with open(urdf_file, 'r') as f:
        robot_desc = f.read()

    return LaunchDescription([
        # Gazebo 空世界
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource([
                os.path.join(
                    get_package_share_directory('gazebo_ros'),
                    'launch', 'empty_world.launch.py'
                )
            ]),
        ),

        # 生成机器人模型
        Node(
            package='gazebo_ros',
            executable='spawn_entity.py',
            name='spawn_model',
            output='screen',
            arguments=[
                '-entity', 'jqr',
                '-topic', 'robot_description',
                '-x', '0.0', '-y', '0.0', '-z', '0.1',
            ],
        ),

        # 关节状态发布
        Node(
            package='joint_state_publisher',
            executable='joint_state_publisher',
            name='joint_state_publisher',
            output='screen',
        ),

        # 机器人状态发布（TF 变换）
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            output='screen',
            parameters=[{'robot_description': robot_desc}],
        ),

        # 发布机器人描述话题（供 spawn_entity 使用）
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher_desc',
            output='screen',
            parameters=[{'robot_description': robot_desc}],
            remappings=[('/robot_description', '/robot_description_topic')],
        ),
    ])

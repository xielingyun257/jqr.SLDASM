cmake_minimum_required(VERSION 3.8)
project(jqr_description)

find_package(ament_cmake REQUIRED)

# 安装所有子目录到包共享目录
install(DIRECTORY
  config
  gestures
  launch
  meshes
  rviz
  urdf
  worlds
  DESTINATION share/${PROJECT_NAME}
)

# 安装 Python 脚本
install(PROGRAMS
  scripts/robot_description_publisher.py
  scripts/gesture_player.py
  scripts/gesture_recorder.py
  DESTINATION lib/${PROJECT_NAME}
)

ament_package()

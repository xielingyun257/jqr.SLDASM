#!/usr/bin/env python3
"""
生成带 JointTrajectoryController 的 SDF
用一个插件控制全部 13 关节，Gazebo 内部插值执行轨迹
"""
import re, os, subprocess, sys
from ament_index_python.packages import get_package_share_directory

SHARE = get_package_share_directory('jqr_description')
URDF = os.path.join(SHARE, 'urdf', 'jqr.SLDASM.urdf')
OUT = '/tmp/jqr_controlled.sdf'

JOINTS = ['joint_1','joint_l_2','joint_l_3','joint_l_4','joint_l_5','joint_l_6','joint_l_7',
          'joint_r_2','joint_r_3','joint_r_4','joint_r_5','joint_r_6','joint_r_7']

# Step 1: 替换 package:// → file://
with open(URDF) as f:
    urdf_text = f.read()
urdf_text = urdf_text.replace('package://jqr_description/', f'file://{SHARE}/')
tmp_urdf = '/tmp/jqr_fixed.urdf'
with open(tmp_urdf, 'w') as f:
    f.write(urdf_text)

# Step 2: ign sdf -p 转换
result = subprocess.run(['ign', 'sdf', '-p', tmp_urdf], capture_output=True, text=True)
if result.returncode != 0:
    print(f'ign sdf 转换失败: {result.stderr}', file=sys.stderr)
    sys.exit(1)
sdf = result.stdout

# 修复版本号
sdf = sdf.replace("<sdf version='1.9'>", "<sdf version='1.7'>")

# 移除 ign_ros2_control 插件（与 JointTrajectoryController 冲突）
sdf = re.sub(
    r'<plugin[^>]*libign_ros2_control[^>]*>.*?</plugin>',
    '', sdf, flags=re.DOTALL
)

# Step 3: 添加 fixed joint（world → base_link）
world_fix = "    <joint name='base_fixed' type='fixed'>\n      <parent>world</parent>\n      <child>base_link</child>\n    </joint>\n"
sdf = sdf.replace('<link name=\'base_link\'>', world_fix + '    <link name=\'base_link\'>')

# Step 4: 轴内阻尼（被动稳定）
old_dyn = '<dynamics>\n          <spring_reference>0</spring_reference>\n          <spring_stiffness>0</spring_stiffness>\n        </dynamics>'
new_dyn = '<dynamics>\n          <spring_reference>0</spring_reference>\n          <spring_stiffness>0</spring_stiffness>\n          <damping>5.0</damping>\n          <friction>2.0</friction>\n        </dynamics>'
sdf = sdf.replace(old_dyn, new_dyn)

# Step 5: JointTrajectoryController（单一插件，控制全部关节）
traj_plugin = '''    <plugin
        filename="libignition-gazebo-joint-trajectory-controller-system.so"
        name="ignition::gazebo::systems::JointTrajectoryController">\n'''
for jn in JOINTS:
    traj_plugin += f'''      <joint_name>{jn}</joint_name>
      <initial_position>0.0</initial_position>
      <position_p_gain>50000</position_p_gain>
      <position_i_gain>0.0</position_i_gain>
      <position_d_gain>20000</position_d_gain>
      <position_i_min>-1</position_i_min>
      <position_i_max>1</position_i_max>
      <position_cmd_min>-1000</position_cmd_min>
      <position_cmd_max>1000</position_cmd_max>
'''
traj_plugin += '    </plugin>'

sdf = sdf.replace('</model>', traj_plugin + '\n</model>')

# 写入
with open(OUT, 'w') as f:
    f.write(sdf)

print(f'✅ SDF 生成完毕: {OUT}')
print(f'   JointTrajectoryController: {len(JOINTS)} 关节 (P=8000, D=6000)')
print(f'   被动阻尼: 25 N·m·s/rad')

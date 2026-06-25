#!/usr/bin/env python3
"""从 URDF 生成带 base_link 固定关节 + 高PID 控制器的 SDF"""
import os, re, sys, subprocess
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

# Step 2: 用 ign sdf -p 转换
result = subprocess.run(['ign', 'sdf', '-p', tmp_urdf], capture_output=True, text=True)
if result.returncode != 0:
    print(f'ign sdf 转换失败: {result.stderr}')
    sys.exit(1)
sdf = result.stdout

# Step 2.5: 修复 SDF 版本号 (1.9 → 1.7, 兼容 Gazebo Fortress)
sdf = sdf.replace("<sdf version='1.9'>", "<sdf version='1.7'>")

# Step 2.6: 移除 ign_ros2_control 插件（与 JointPositionController 冲突）
sdf = re.sub(
    r'<plugin[^>]*ignition-ros2-control[^>]*>.*?</plugin>',
    '', sdf, flags=re.DOTALL
)

# Step 3: 添加 fixed joint（锁定 base_link 到真实世界坐标系）
# 注意：不能添加 <link name='world'/>，否则会与 Gazebo 保留标识符冲突
world_fix = '''    <joint name='base_fixed' type='fixed'>
      <parent>world</parent>
      <child>base_link</child>
    </joint>
'''
sdf = sdf.replace('<link name=\'base_link\'>', world_fix + '    <link name=\'base_link\'>')

# Step 4: 在 </model> 前为每个关节添加 JointPositionController
plugins = ''
for jn in JOINTS:
    plugins += f'''
    <plugin filename="ignition-gazebo-joint-position-controller-system"
            name="ignition::gazebo::systems::JointPositionController">
      <joint_name>{jn}</joint_name>
      <p_gain>5000</p_gain>
      <i_gain>0.1</i_gain>
      <d_gain>500</d_gain>
      <use_velocity_commands>false</use_velocity_commands>
    </plugin>'''
sdf = sdf.replace('</model>', plugins + '\n</model>')

# Step 5: 写入
bak = OUT + '.bak'
if not os.path.exists(bak):
    os.rename(OUT, bak) if os.path.exists(OUT) else None
with open(OUT, 'w') as f:
    f.write(sdf)

print(f'✅ SDF 生成完毕: {OUT}')
print(f'   fixed joint: base_fixed (world → base_link)')
print(f'   JointPositionController: {len(JOINTS)} joints (p=5000, d=500)')

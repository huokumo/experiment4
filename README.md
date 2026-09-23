# 实验4：感知设备校准与适配调试

本仓库是 ROS 2 Humble 与 Gazebo Classic 11 课程实验功能包。在实验3完成传感器安装的基础上，完成三维激光雷达外参校准、IMU静止零偏补偿和相机接口适配。

当前仓库只包含可运行工程和试跑说明。完整实验指导书将在工程实机试跑通过、验收阈值确定后编写。

## 环境

- Ubuntu 22.04 x86_64
- ROS 2 Humble
- Gazebo Classic 11
- RViz2
- Python 3

推荐工作空间：

```text
/root/exp4/experiment4_ws
```

## 编译

```bash
mkdir -p /root/exp4/experiment4_ws/src
cd /root/exp4/experiment4_ws/src
git clone https://github.com/huokumo/experiment4.git

cd /root/exp4/experiment4_ws
source /opt/ros/humble/setup.bash
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install --packages-select experiment4
source install/setup.bash
```

## 三种启动模式

故障基线：

```bash
ros2 launch experiment4 calibration_fault.launch.py
```

学生调试：

```bash
ros2 launch experiment4 calibration_student.launch.py
```

教师答案验证：

```bash
ros2 launch experiment4 calibration_solution.launch.py
```

如不需要自动打开RViz，在任一启动命令后添加：

```text
rviz:=false
```

## 学生编辑文件

学生只修改：

```text
config/sensor_calibration_student.yaml
```

该文件初始包含三类故障：

1. `mid360_calibrated` 外参存在平移和旋转偏差；
2. IMU补偿参数为零，无法消除注入的固定零偏；
3. 相机适配器订阅了错误的设备话题。

修改YAML后需要停止并重新启动仿真，使参数生效。

## 雷达外参评估

RViz中绿色点云是实验3原始参考数据，红色点云是候选外参结果。修改参数并重启后运行：

```bash
ros2 run experiment4 evaluate_lidar_extrinsic.py
```

当前暂定阈值为平移残差不超过 `0.02 m`、旋转残差不超过 `0.02 rad`。阈值将在Ubuntu目标环境完整试跑后确认。

## IMU样本采集和零偏计算

采样期间保持机器人静止：

```bash
ros2 run experiment4 collect_imu_samples.py --ros-args \
  -p topic:=/vendor/imu/data_raw \
  -p sample_count:=500 \
  -p output_file:=/tmp/imu_samples.csv

ros2 run experiment4 calculate_imu_bias.py /tmp/imu_samples.csv
```

将计算结果填入 `imu_bias_corrector` 对应参数。程序默认静止时Z轴线加速度为 `9.81 m/s^2`，可用 `--expected-z` 修改。

## 自动验收

保持学生版或答案版仿真运行，在新终端执行：

```bash
source /opt/ros/humble/setup.bash
source /root/exp4/experiment4_ws/install/setup.bash
ros2 run experiment4 verify_calibration.py
```

答案版应输出：

```text
Result: 8/8 passed
```

故障版应明确显示雷达外参、IMU补偿和相机标准接口未通过。

## 主要话题

| 类型 | 原始/设备话题 | 校准或标准话题 |
|---|---|---|
| 雷达 | `/mid360/points` | `/perception/lidar/points` |
| IMU | `/vendor/imu/data_raw` | `/perception/imu/data` |
| 相机图像 | `/vendor_camera/color` | `/perception/camera/image_raw` |
| 相机信息 | `/vendor_camera/info` | `/perception/camera/camera_info` |

实验3的物理安装坐标保持不变：相机 `0.38 0 0.68`、雷达 `0 0 0.68`、IMU `-0.28 0 0.59`。

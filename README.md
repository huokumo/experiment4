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
# rosdep init/update requires network access; if it times out and dependencies are installed, continue to colcon.
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install --packages-select experiment4
source install/setup.bash
```

## 唯一启动入口

```bash
ros2 launch experiment4 calibration.launch.py
```

如不需要自动打开RViz，添加：

```text
rviz:=false
```

## 唯一配置文件

学生只修改：

```text
config/sensor_calibration.yaml
```

按顺序逐项处理，该文件初始包含三类待解决问题：

1. `mid360_calibrated` 外参存在平移和旋转偏差；
2. IMU补偿参数为零，无法消除注入的固定零偏；
3. 相机适配器订阅了错误的设备话题。

每完成一项，修改此文件，停止仿真，重新编译并用同一个命令启动。

更新现有仓库后，先清除旧安装结果再重新编译，确保脚本可执行权限更新：

```bash
cd /root/exp4/experiment4_ws/src/experiment4
git pull origin main
cd /root/exp4/experiment4_ws
rm -rf build/experiment4 install/experiment4
source /opt/ros/humble/setup.bash
colcon build --symlink-install --packages-select experiment4
source install/setup.bash
```

## 雷达外参评估

RViz中绿色点云是实验3原始参考数据，红色点云是候选外参结果。修改参数并重启后运行：

```bash
ros2 run experiment4 evaluate_lidar_extrinsic
```

当前暂定阈值为平移残差不超过 `0.02 m`、旋转残差不超过 `0.02 rad`。阈值将在Ubuntu目标环境完整试跑后确认。

## IMU样本采集和零偏计算

采样期间保持机器人静止：

```bash
ros2 run experiment4 collect_imu_samples --ros-args \
  -p topic:=/vendor/imu/data_raw \
  -p sample_count:=500 \
  -p output_file:=/tmp/imu_samples.csv

ros2 run experiment4 calculate_imu_bias /tmp/imu_samples.csv
```

将计算结果填入 `imu_bias_corrector` 对应参数。程序默认静止时Z轴线加速度为 `9.81 m/s^2`，可用 `--expected-z` 修改。

## 自动验收

保持当前仿真运行，在新终端执行：

```bash
source /opt/ros/humble/setup.bash
source /root/exp4/experiment4_ws/install/setup.bash
ros2 run experiment4 verify_calibration
```

三项任务全部完成后应输出：

```text
Result: 8/8 passed
```


## 主要话题

| 类型 | 原始/设备话题 | 校准或标准话题 |
|---|---|---|
| 雷达 | `/mid360/points` | `/perception/lidar/points` |
| IMU | `/vendor/imu/data_raw` | `/perception/imu/data` |
| 相机图像 | `/vendor_camera/color` | `/perception/camera/image_raw` |
| 相机信息 | `/vendor_camera/info` | `/perception/camera/camera_info` |

实验3的物理安装坐标保持不变：相机 `0.38 0 0.68`、雷达 `0 0 0.68`、IMU `-0.28 0 0.59`。

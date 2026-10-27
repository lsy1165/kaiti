# 阶段 4：复杂工况样例目录

本目录用于准备复杂工况实验数据。

## 核心规则

本阶段采用“多个原始样例，一一对应多种复杂工况”的方式：

```text
原始样例 A -> 弱光
原始样例 B -> 雾天
原始样例 C -> 运动模糊
原始样例 D -> 图像噪声
原始样例 E -> 点云稀疏
原始样例 F -> 点云扰动
```

不采用“同一帧样例生成多个复杂工况”的一对多方式。

## 当前工况含义

当前阶段的复杂工况不是随意改图，而是对应自动驾驶和移动机器人感知中常见的传感器退化问题：

1. `low_light`：弱光，模拟夜晚、隧道、阴影或曝光不足导致图像亮度下降。
2. `fog`：雾天，模拟雾、霾、雨雾等造成图像对比度下降和远处目标不清晰。
3. `motion_blur`：运动模糊，模拟车辆高速运动、目标快速移动、相机曝光时间较长或车身颠簸造成的画面模糊。
4. `image_noise`：图像噪声，模拟弱光高增益、镜头污染、雨雪灰尘或图像压缩传输造成的颗粒和杂色。
5. `lidar_sparse`：点云稀疏，模拟远距离目标、低线束雷达、恶劣天气回波丢失、弱反射表面或雷达局部失效造成的雷达点减少。
6. `lidar_jitter`：点云扰动，模拟雷达测距误差、车辆振动、时间同步误差、外参标定误差、异常回波或设备漂移造成的点云位置偏移。

其中 `motion_blur` 和 `image_noise` 主要影响相机图像，`lidar_sparse` 和 `lidar_jitter` 主要影响激光雷达点云。它们可以用来分析多模态三维检测中不同传感器信息退化后对检测稳定性的影响。

## base_samples

`base_samples/` 用来放干净原始多模态样例，每个样例必须包含三件套：

```text
样例ID.png
样例ID.bin
样例ID.pkl
```

其中：

1. `.png` 是相机图像；
2. `.bin` 是同一帧激光雷达点云；
3. `.pkl` 是多模态检测所需的标定/元数据信息。

## condition_samples

`condition_samples/` 保存生成后的复杂工况样例。生成脚本会保证每个原始样例最多只对应一种复杂工况。

## paired_samples

`paired_samples/` 是后续展示和服务器检测优先使用的成组目录。每个对比组单独一个文件夹，内部固定分为：

```text
paired_samples/
  对比组ID/
    clean/      # 改变前原始图像、点云、pkl
    complex/    # 改变后复杂工况图像、点云、pkl
    pair_info.json
```

这样能保证改变前和改变后的数据不会混在一起，后续检测结果也可以按同样结构保存。

## 生成命令

如果已经放入多个原始样例，在项目根目录运行：

```powershell
conda activate py39
python code/src/stage04_complex_conditions/create_one_to_one_conditions.py
```

如果只是先用阶段 3 已有的 `000008` 做一次链路测试，可以运行：

```powershell
conda activate py39
python code/src/stage04_complex_conditions/create_one_to_one_conditions.py --bootstrap-stage03-sample
```

注意：链路测试只会生成一个复杂工况样例，不会把 `000008` 扩展成多种复杂工况。

## 检测结果整理

服务器批量检测脚本会读取 `paired_samples/`，并把结果保存为：

```text
code/outputs/stage04_complex_conditions/mvxnet_comparison_results/
  对比组ID/
    clean/      # 改变前检测结果
    complex/    # 改变后检测结果
```

服务器结果复制回本地后，可生成检测结果对比图：

```powershell
conda activate py39
python code/src/stage04_complex_conditions/make_detection_comparison_previews.py
```

当前检测结果已整理到：

```text
code/outputs/stage04_complex_conditions/detection_comparisons/
```

从当前结果看，弱光和雾天样例影响相对较轻，适合作为辅助展示；运动模糊、图像噪声、点云稀疏和点云扰动会带来更明显的可靠性下降，例如高置信目标减少、少量漏检或平均置信度下降，更适合作为复杂工况研究必要性的主要说明样例。

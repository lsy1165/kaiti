# KITTI 数据准备清单

本文件用于阶段 2：单模态三维目标检测系统复现。

当前课题为“复杂工况下三维目标检测方法研究”，阶段 2 优先采用 KITTI Object Detection 数据集和 PointPillars/CenterPoint 等点云三维目标检测模型。

## 一、为什么先准备 KITTI

KITTI 3D Object Detection Benchmark 是自动驾驶三维目标检测中常用的公开基准。官方说明中，该 3D 目标检测基准包含 7481 张训练图像、7518 张测试图像以及对应的点云数据，并提供三维目标检测和鸟瞰图评价相关开发工具。

本阶段先使用 KITTI 的原因是：

1. 数据规模比 nuScenes 更小，更适合先跑通基础三维检测流程；
2. 数据组织方式清晰，便于理解点云、图像、标定和标签之间的关系；
3. PointPillars、SECOND、PointRCNN、CenterPoint 等模型均支持或可转换支持 KITTI；
4. 为后续复现图像+雷达多模态三维目标检测基础系统打好点云处理基础。

## 二、需要下载的 KITTI 文件

请从 KITTI 官方 Object Detection / 3D Object Detection 页面下载以下内容。

阶段 2 最少需要：

| 文件 | 用途 | 是否必须 |
|---|---|---|
| `data_object_velodyne.zip` | 激光雷达点云数据 | 必须 |
| `data_object_calib.zip` | 相机和雷达标定数据 | 必须 |
| `data_object_label_2.zip` | 训练集目标标签 | 必须 |
| `data_object_image_2.zip` | 左目彩色图像 | 建议下载 |

说明：

1. 如果只做点云单模态三维检测，核心输入是 `velodyne` 点云；
2. `calib` 和 `label_2` 对三维检测训练、评估和可视化很重要，建议一起准备；
3. `image_2` 暂时不是点云单模态检测的核心输入，但它有助于后续展示场景图像、检查目标标签，以及衔接图像+雷达多模态三维检测系统。

## 三、压缩包放置位置

下载完成后，请将压缩包放到：

```text
code/data/stage02_mono3d_detection/downloads/
```

建议保持以下文件名：

```text
data_object_velodyne.zip
data_object_calib.zip
data_object_label_2.zip
data_object_image_2.zip
```

## 四、自动解压整理

压缩包放好后，可以先检查下载状态：

```powershell
conda activate py39
python code/src/stage02_mono3d_detection/check_kitti_archives.py
```

检查报告会生成到：

```text
code/outputs/stage02_mono3d_detection/kitti_archive_check.md
```

确认压缩包齐全后，在项目根目录运行：

```powershell
conda activate py39
python code/src/stage02_mono3d_detection/prepare_kitti_archives.py
```

整理后，目标目录应为：

```text
code/data/stage02_mono3d_detection/kitti/
├── training/
│   ├── velodyne/
│   ├── image_2/
│   ├── calib/
│   └── label_2/
└── testing/
    ├── velodyne/
    ├── image_2/
    └── calib/
```

## 五、数据检查

解压整理后，运行：

```powershell
conda activate py39
python code/src/stage02_mono3d_detection/check_kitti_dataset.py --config code/configs/stage02_mono3d_kitti.yaml
```

检查报告会生成到：

```text
code/outputs/stage02_mono3d_detection/kitti_dataset_check.md
```

报告中需要重点看：

1. `training/velodyne` 是否存在；
2. `training/calib` 是否存在；
3. `training/label_2` 是否存在；
4. 点云、图像、标定、标签的样本 ID 是否能对齐；
5. 是否能成功读取第一帧点云。

## 六、点云 BEV 可视化

数据检查通过后，运行：

```powershell
conda activate py39
python code/src/stage02_mono3d_detection/visualize_kitti_bev.py --config code/configs/stage02_mono3d_kitti.yaml
```

如果要指定样本，例如 `000000`，运行：

```powershell
conda activate py39
python code/src/stage02_mono3d_detection/visualize_kitti_bev.py --config code/configs/stage02_mono3d_kitti.yaml --sample-id 000000
```

输出的 BEV 图会保存到：

```text
code/outputs/stage02_mono3d_detection/
```

如果要同时检查点云和三维目标标签框是否能够可视化，运行：

```powershell
conda activate py39
python code/src/stage02_mono3d_detection/visualize_kitti_bev_with_labels.py --config code/configs/stage02_mono3d_kitti.yaml
```

该脚本会读取 `label_2` 和 `calib`，将 KITTI 相机坐标系中的三维标签转换到雷达坐标系下，并在 BEV 图中绘制目标框。

## 七、当前阶段不做的事

为了保持步骤清晰，当前阶段暂时不做：

1. 不直接训练 PointPillars；
2. 不直接安装完整 MMDetection3D 或 OpenPCDet；
3. 不直接构造复杂工况数据；
4. 不直接复现图像+雷达多模态三维检测系统；
5. 不直接写创新算法。

当前只完成：

1. KITTI 数据准备；
2. KITTI 数据结构检查；
3. KITTI 点云读取；
4. KITTI 点云 BEV 可视化。

这些完成后，再进入 PointPillars 或 CenterPoint 的模型复现。单模态三维检测跑通后，再进入图像+雷达多模态三维检测基础系统复现。

## 八、参考来源

1. KITTI 3D Object Detection Benchmark 官方页面：  
   https://www.cvlibs.net/datasets/kitti/eval_object.php?obj_benchmark=3d

2. KITTI 官方页面说明该 3D 目标检测基准包含训练图像、测试图像及对应点云，并提供 Velodyne 点云、相机标定矩阵、训练标签和开发工具等下载项。

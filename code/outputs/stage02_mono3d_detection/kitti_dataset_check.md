# 阶段 2 KITTI 数据检查报告

## 数据根目录

`code\data\stage02_mono3d_detection\kitti`

## training 目录检查

| 子目录 | 是否存在 | 文件数量 |
|---|---|---:|
| velodyne | 否 | 0 |
| image_2 | 否 | 0 |
| calib | 否 | 0 |
| label_2 | 否 | 0 |

## 样本 ID 对齐检查

- 点云样本数：0
- 图像样本数：0
- 标定样本数：0
- 标签样本数：0
- 四类文件均存在的训练样本数：0

未找到点云文件，暂不能读取点云样例。

## testing 目录检查

| 子目录 | 是否存在 | 文件数量 |
|---|---|---:|
| velodyne | 否 | 0 |
| image_2 | 否 | 0 |
| calib | 否 | 0 |

## 结论

当前尚未检测到完整 KITTI training 样本。请先按说明整理 KITTI 数据，再继续三维检测模型复现。

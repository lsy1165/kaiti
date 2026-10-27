# 阶段 2 KITTI 数据检查报告

## 数据根目录

`code\data\stage02_mono3d_detection\kitti_synthetic`

## training 目录检查

| 子目录 | 是否存在 | 文件数量 |
|---|---|---:|
| velodyne | 是 | 1 |
| image_2 | 是 | 1 |
| calib | 是 | 1 |
| label_2 | 是 | 1 |

## 样本 ID 对齐检查

- 点云样本数：1
- 图像样本数：1
- 标定样本数：1
- 标签样本数：1
- 四类文件均存在的训练样本数：1

点云样例 000000.bin 可读取，点数：12950。

## testing 目录检查

| 子目录 | 是否存在 | 文件数量 |
|---|---|---:|
| velodyne | 否 | 0 |
| image_2 | 否 | 0 |
| calib | 否 | 0 |

## 结论

KITTI training 数据结构基本可用，可以继续进行点云 BEV 可视化和三维检测模型复现。

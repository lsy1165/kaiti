# 阶段 2 三维检测环境检查报告

## 基本环境

- Python：3.9.0
- Python 路径：`D:\Users\27452\anaconda3\envs\py39\python.exe`
- 操作系统：Windows-10-10.0.26100-SP0

## PyTorch/CUDA 状态

- torch 版本：2.8.0+cpu
- CUDA 是否可用：False
- torch CUDA 版本：None
- CUDA 设备数量：0
- 当前 PyTorch 不能调用 CUDA，完整 3D 检测训练/推理可能需要重新配置 GPU 环境或使用服务器。

## nvidia-smi 状态

- 未在 PATH 中找到 nvidia-smi。

## 关键 Python 包

| 包 | 状态 |
|---|---|
| torch | 2.8.0 |
| torchvision | 0.23.0 |
| numpy | 2.0.2 |
| matplotlib | 3.9.4 |
| spconv-cu120 | 未安装 |
| spconv-cu118 | 未安装 |
| spconv | 未安装 |
| open3d | 未安装 |
| mmdet | 未安装 |
| mmcv | 未安装 |
| mmdet3d | 未安装 |
| pcdet | 未安装 |

## 判断

当前环境可以继续进行 KITTI 数据检查、点云读取、BEV 可视化和标签框可视化。
若要复现 PointPillars/CenterPoint 等三维检测模型，通常还需要：

1. 可用的 NVIDIA GPU 与 CUDA 版 PyTorch；
2. spconv 等稀疏卷积依赖；
3. OpenPCDet 或 MMDetection3D 等三维检测框架；
4. 完整 KITTI 数据集。

按照老师意见，下一阶段应先完成单模态三维检测基础系统复现，再进入图像+雷达多模态三维检测基础系统。

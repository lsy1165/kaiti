# 阶段 2 数据说明

本阶段面向“复杂工况下三维目标检测方法研究”，先以 KITTI 三维目标检测数据为基础，复现点云单模态三维目标检测流程。

注意：当前阶段只做单模态三维目标检测基础系统准备与复现，不做复杂工况退化实验。按照导师意见，应在单模态三维检测之后，再复现图像+雷达多模态三维目标检测基础系统；恶劣工况实验放在基础系统跑通之后。

详细下载和整理步骤见：

```text
KITTI数据准备清单.md
```

请将 KITTI object detection 数据整理为以下结构：

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

当前阶段先检查 `training/velodyne` 点云文件，并生成 BEV 俯视可视化图。等数据链路确认后，再接入 PointPillars 或 CenterPoint。

如果已经下载了 KITTI object detection 压缩包，可以先放入：

```text
code/data/stage02_mono3d_detection/downloads/
```

建议文件名保持为：

```text
data_object_velodyne.zip
data_object_image_2.zip
data_object_calib.zip
data_object_label_2.zip
```

然后运行数据整理脚本，将其解压到本阶段约定的数据目录。

另外，本阶段提供 `kitti_synthetic/` 作为合成点云样例目录，只用于验证点云读取和 BEV 可视化链路，不作为论文实验数据。

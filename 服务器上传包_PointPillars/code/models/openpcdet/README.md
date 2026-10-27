# OpenPCDet 模型权重目录

本目录用于存放服务器复现 PointPillars 时使用的模型权重。当前项目已包含检测展示所需的预训练权重。

默认文件名：

```text
pointpillar_kitti.pth
```

服务器脚本默认读取：

```text
code/models/openpcdet/pointpillar_kitti.pth
```

如果实际权重文件名不同，可以在服务器运行前设置：

```bash
export CKPT_PATH=/path/to/your/checkpoint.pth
```

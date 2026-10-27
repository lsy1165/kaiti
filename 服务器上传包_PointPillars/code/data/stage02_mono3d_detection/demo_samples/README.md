# demo 点云目录

本目录用于 PointPillars 检测展示版。

默认基础 demo 点云文件名：

```text
000008.bin
```

当前项目已包含该 demo 点云，并额外生成了若干用于批量检测展示的点云变体。服务器脚本 `03_prepare_demo_assets.sh` 会先检查基础点云是否存在；如果不存在，会尝试自动下载，然后生成多帧 demo 变体。也可以手动把 KITTI 格式点云文件放到这里，并保持文件名为 `000008.bin`，或在服务器运行前设置：

```bash
export DEMO_DATA_PATH=/path/to/your/sample.bin
```

该目录只用于检测展示，不用于训练。除 `000008.bin` 外的变体不是独立 KITTI 场景，不作为正式实验数据。

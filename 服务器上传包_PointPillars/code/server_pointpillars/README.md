# 服务器复现 PointPillars 检测展示说明

本目录用于在 Linux GPU 服务器上复现单模态三维目标检测基础系统。当前采用“检测展示版”，不训练模型，不要求完整 KITTI 数据。

目标路线：

```text
demo 点云 + OpenPCDet + PointPillars 预训练权重
```

完成后可展示：

1. 输入：多帧 KITTI 格式 demo 点云；
2. 模型：PointPillars；
3. 输出：三维检测框、置信度和 BEV 检测图。

## 推荐脚本顺序

```text
00_check_server.sh
01_create_conda_env.sh
02_install_openpcdet.sh
03_prepare_demo_assets.sh
05_run_pointpillar_demo.sh
```

也可以直接运行：

```bash
bash code/server_pointpillars/08_quick_demo_only.sh
```

## 检测展示版需要的内容

上传包中已经包含：

```text
code/data/stage02_mono3d_detection/demo_samples/*.bin
code/models/openpcdet/pointpillar_kitti.pth
```

如果 demo 点云被删除，`03_prepare_demo_assets.sh` 会尝试联网重新下载基础点云，并生成多帧 demo 变体。

## 可选完整 KITTI 流程

后续如需完整测试或训练，再使用：

```text
03_link_kitti_data.sh
04_prepare_kitti_infos.sh
06_test_pointpillar_ckpt.sh
07_train_pointpillar.sh
```

开题阶段优先完成检测展示，不强求训练。

## 官方参考

- OpenPCDet: https://github.com/open-mmlab/OpenPCDet
- OpenPCDet 安装文档: https://github.com/open-mmlab/OpenPCDet/blob/master/docs/INSTALL.md
- OpenPCDet Demo: https://github.com/open-mmlab/OpenPCDet/blob/master/docs/DEMO.md

# 开题实验代码

本目录用于存放开题后续实验代码，按照行动方案分阶段推进。

当前进度：

1. 阶段 1：二维目标检测 Demo 已跑通；
2. 阶段 2：单模态三维目标检测展示已跑通，当前路线为 `PointPillars + KITTI 格式点云`；
3. 阶段 3：图像+雷达多模态三维目标检测展示已跑通，当前路线为 `MVX-Net + MMDetection3D + KITTI 格式样例`；
4. 阶段 4：复杂工况样例构造和初步检测对比已完成，采用“多个原始样例一对一构造多种复杂工况”的策略。

## 阶段 1 目标

先跑通最基础的二维目标检测流程，理解：

1. 图片如何输入模型；
2. 模型如何输出检测框、类别和置信度；
3. 检测结果如何保存为图片和 JSON；
4. 后续如何把该流程迁移到单模态三维检测和图像+雷达多模态三维检测。

## 阶段 1 文件

请先阅读：

1. `代码结构说明.md`
2. `configs/stage01_2d_detection.yaml`
3. `src/stage01_2d_detection/run_yolo_demo.py`

## 阶段 1 运行前准备

当前脚本使用 YOLO 作为二维检测 Demo。

已检查本机 conda 环境，`py39` 环境中已经具备第一阶段需要的主要依赖：

1. `ultralytics`
2. `opencv-python`
3. `torch`
4. `torchvision`

因此建议优先使用：

```powershell
conda activate py39
```

如果后续需要重新创建独立环境，可以参考：

```powershell
conda env create -f code/environment.stage01.yml
conda activate kaiti-stage01
```

如果本机没有模型权重，`ultralytics` 在使用 `yolov8n.pt` 时通常会尝试自动下载权重。若无法联网，可以手动下载权重后，把路径写入配置文件的 `model.weights` 字段。

## 阶段 1 基本运行方式

把待检测图片放入：

```text
code/data/stage01_2d_detection/input_images/
```

然后在项目根目录运行：

```powershell
conda activate py39
python code/src/stage01_2d_detection/run_yolo_demo.py --config code/configs/stage01_2d_detection.yaml
```

结果会输出到：

```text
code/outputs/stage01_2d_detection/
```

生成检测结果后，可以继续整理汇总：

```powershell
conda activate py39
python code/src/stage01_2d_detection/summarize_results.py
```

汇总文件会保存为：

```text
code/outputs/stage01_2d_detection/summary.md
```

## 阶段 1 进度

已完成：

1. 创建代码根目录；
2. 创建二维检测 Demo 目录结构；
3. 编写二维检测入口脚本；
4. 编写配置文件；
5. 编写代码结构说明；
6. 编写二维检测结果汇总脚本。

阶段 1 已完成：

1. 已准备测试图片；
2. 已确认 `py39` 环境具备依赖；
3. 已跑通二维检测 Demo；
4. 已保存可视化结果；
5. 已生成检测结果 JSON；
6. 已生成检测结果 Markdown 汇总。

## 阶段 2：单模态三维目标检测

阶段 2 选择 `PointPillars + KITTI 格式点云` 作为优先路线。当前已经完成服务器端检测展示，能够输入点云、运行 PointPillars 预训练模型，并输出 BEV 检测图和结构化检测结果。

检查三维检测环境：

```powershell
conda activate py39
python code/src/stage02_mono3d_detection/check_3d_detection_env.py
```

KITTI 下载和整理步骤见：

```text
code/data/stage02_mono3d_detection/KITTI数据准备清单.md
```

如果已经下载 KITTI object detection 压缩包，可先放入：

```text
code/data/stage02_mono3d_detection/downloads/
```

然后整理压缩包：

```powershell
conda activate py39
python code/src/stage02_mono3d_detection/check_kitti_archives.py
python code/src/stage02_mono3d_detection/prepare_kitti_archives.py
```

检查 KITTI 数据结构：

```powershell
conda activate py39
python code/src/stage02_mono3d_detection/check_kitti_dataset.py --config code/configs/stage02_mono3d_kitti.yaml
```

生成 KITTI 点云 BEV 可视化：

```powershell
conda activate py39
python code/src/stage02_mono3d_detection/visualize_kitti_bev.py --config code/configs/stage02_mono3d_kitti.yaml
```

生成带三维标签框的 BEV 可视化：

```powershell
conda activate py39
python code/src/stage02_mono3d_detection/visualize_kitti_bev_with_labels.py --config code/configs/stage02_mono3d_kitti.yaml
```

当前如果没有放入 KITTI 数据，检查脚本会生成缺失报告，BEV 可视化脚本会提示找不到点云文件。数据放好后再运行即可。阶段 2 的目标是跑通单模态三维检测基础系统，不进行复杂工况实验。

在正式 KITTI 数据尚未放入前，可以生成一个合成 KITTI 风格样例，只用于检查点云读取和 BEV 可视化程序：

```powershell
conda activate py39
python code/src/stage02_mono3d_detection/create_synthetic_kitti_sample.py
python code/src/stage02_mono3d_detection/check_kitti_dataset.py --config code/configs/stage02_synthetic_kitti.yaml
python code/src/stage02_mono3d_detection/visualize_kitti_bev.py --config code/configs/stage02_synthetic_kitti.yaml
python code/src/stage02_mono3d_detection/visualize_kitti_bev_with_labels.py --config code/configs/stage02_synthetic_kitti.yaml
```

服务器 PointPillars 检测展示结果已经保存到：

```text
code/outputs/server_pointpillars_demo/
```

该目录包含 9 张 `*_pred_bev.png` BEV 检测图、`predictions.json` 检测结果和 `inference.log` 推理日志。当前阶段 2 可作为“单模态三维目标检测基础系统已跑通”的展示材料。

## 阶段 3：图像+雷达多模态三维检测

阶段 3 目标是复现一个图像+雷达多模态三维目标检测基础系统，完成部署展示效果。当前已采用 `MVX-Net + MMDetection3D + KITTI 格式样例` 跑通检测展示流程。

当前已完成：

1. 整理同一帧样例中的相机图像、激光雷达点云和元数据信息；
2. 通过脚本检查三者对应关系；
3. 基于 MVX-Net 完成图像+雷达多模态三维目标检测推理；
4. 生成相机视角检测展示图和结构化检测结果。

阶段 3 路线说明：

```text
code/data/stage03_multimodal3d_detection/阶段3_多模态检测路线说明.md
```

阶段 3 样例检查：

```powershell
conda activate py39
python code/src/stage03_multimodal3d_detection/check_multimodal_demo_assets.py
```

检查报告：

```text
code/outputs/stage03_multimodal3d_detection/demo_assets_check.md
```

多模态检测展示结果已经保存到：

```text
code/outputs/stage03_mvxnet_demo/
```

其中主要展示图为：

```text
code/outputs/stage03_mvxnet_demo/vis_camera/CAM2/000008.png
```

结构化检测结果为：

```text
code/outputs/stage03_mvxnet_demo/preds/000008.json
```

日志显示结果已正常保存，结构化结果中包含 11 个三维检测框。当前阶段 3 可作为“图像+雷达多模态三维目标检测基础系统已跑通”的展示材料。

在阶段 3 基础系统复现完成后，已进入阶段 4 复杂工况样例构造和检测退化分析。

服务器端 MVX-Net 检测展示脚本和说明在：

```text
code/server_mvxnet/
服务器上传包_MVXNet/
```

后续如果需要复现实验，可继续使用该上传包；如果只进行开题展示，优先使用已经复制回本地的 `code/outputs/stage03_mvxnet_demo/` 结果。

## 阶段 4：复杂工况样例与检测对比

阶段 4 采用“多个原始样例，一一对应多种复杂工况”的策略，不使用同一帧生成多种复杂工况。

当前已建立阶段 4 数据结构和生成脚本：

```text
code/data/stage04_complex_conditions/
code/src/stage04_complex_conditions/create_one_to_one_conditions.py
code/configs/stage04_complex_conditions.yaml
```

当前已经准备 6 组 clean/complex 复杂工况对比数据：

```text
000008_low_light
000021_fog
000022_motion_blur
000023_image_noise
000024_lidar_sparse
000025_lidar_jitter
```

成组对比数据目录：

```text
code/data/stage04_complex_conditions/paired_samples/
```

每组内部都有 `clean/` 和 `complex/`，分别保存改变前原始数据和改变后复杂工况数据。

生成报告：

```text
code/outputs/stage04_complex_conditions/complex_condition_samples_report.md
```

服务器可以直接读取 `paired_samples/` 进行 clean/complex 批量检测。

服务器检测结果将按同样的 clean/complex 结构保存：

```text
code/outputs/stage04_complex_conditions/mvxnet_comparison_results/对比组ID/clean/
code/outputs/stage04_complex_conditions/mvxnet_comparison_results/对比组ID/complex/
```

当前服务器检测结果已经复制回本地，并生成了 6 张改变前/改变后的检测对比图：

```text
code/outputs/stage04_complex_conditions/detection_comparisons/
```

当前验收结论是：弱光和雾天样例影响相对较轻，可以作为辅助展示；运动模糊、图像噪声、点云稀疏和点云扰动对检测可靠性影响更明显，表现为高置信目标减少、少量漏检或平均置信度下降，更适合作为说明复杂工况研究必要性的主要样例。后续不能简单表述为“所有复杂工况都导致检测失败”，应表述为“复杂工况会造成不同程度的检测可靠性下降”。

## 服务器复现 PointPillars

当前 Windows 本机环境没有可用 CUDA 版 PyTorch，也没有完整三维检测框架，因此 PointPillars 复现建议放到 Linux GPU 服务器上进行。

当前服务器路线为“检测展示版”：使用多帧 demo 点云和 PointPillars 预训练权重做推理展示，不训练模型，也不要求完整 KITTI 数据。

服务器脚本和操作说明在：

```text
code/server_pointpillars/
```

重点阅读：

```text
code/server_pointpillars/服务器操作指南.md
```

上传服务器时至少需要：

```text
code/server_pointpillars/
code/data/stage02_mono3d_detection/demo_samples/
code/models/openpcdet/
```

服务器运行完成后，结果需要复制回本地：

```text
code/outputs/server_pointpillars_demo/
```

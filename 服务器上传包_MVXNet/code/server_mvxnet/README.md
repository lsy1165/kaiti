# MVX-Net Server Demo

This folder contains server-side scripts for the stage 03 multimodal 3D detection demo.

Route:

```text
KITTI-format image + point cloud -> MMDetection3D -> MVX-Net -> multimodal 3D detection output
```

Recommended order:

```bash
bash code/server_mvxnet/00_check_server.sh
bash code/server_mvxnet/01_install_mmdetection3d.sh
bash code/server_mvxnet/02_prepare_demo_assets.sh
bash code/server_mvxnet/03_run_mvxnet_demo.sh
```

The output directory is:

```text
code/outputs/stage03_mvxnet_demo/
```

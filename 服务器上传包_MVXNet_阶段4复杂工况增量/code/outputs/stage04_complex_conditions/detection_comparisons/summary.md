# 阶段 4 检测结果对比图生成报告

本报告用于整理复杂工况前后 MVX-Net 多模态三维检测结果。需要注意：检测数量没有明显下降，并不等于复杂工况没有影响；置信度下降、高置信目标减少和个别漏检都说明模型判断稳定性下降。

| 对比组 | 状态 | 检测数量 clean->complex | 平均置信度 clean->complex | >=0.5 数量 clean->complex | >=0.7 数量 clean->complex | 结果判断 | 对比图 |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| `000008_low_light` | ok | 11->11 | 0.64->0.59 | 7->7 | 5->5 | 影响较轻，可作为辅助样例 | `code\outputs\stage04_complex_conditions\detection_comparisons\000008_low_light_clean_vs_complex_detection.png` |
| `000021_fog` | ok | 12->12 | 0.53->0.48 | 7->6 | 5->4 | 影响较轻到中等，高置信目标略少 | `code\outputs\stage04_complex_conditions\detection_comparisons\000021_fog_clean_vs_complex_detection.png` |
| `000022_motion_blur` | ok | 4->4 | 0.38->0.25 | 2->1 | 0->0 | 可靠性下降，能说明图像退化影响 | `code\outputs\stage04_complex_conditions\detection_comparisons\000022_motion_blur_clean_vs_complex_detection.png` |
| `000023_image_noise` | ok | 3->2 | 0.30->0.32 | 1->0 | 0->0 | 出现漏检，能支撑复杂工况分析 | `code\outputs\stage04_complex_conditions\detection_comparisons\000023_image_noise_clean_vs_complex_detection.png` |
| `000024_lidar_sparse` | ok | 4->3 | 0.55->0.56 | 2->2 | 2->1 | 出现漏检，能说明点云信息缺失影响 | `code\outputs\stage04_complex_conditions\detection_comparisons\000024_lidar_sparse_clean_vs_complex_detection.png` |
| `000025_lidar_jitter` | ok | 11->11 | 0.61->0.33 | 8->3 | 4->0 | 高置信目标明显减少，研究价值较强 | `code\outputs\stage04_complex_conditions\detection_comparisons\000025_lidar_jitter_clean_vs_complex_detection.png` |

## 验收结论

本批结果可以用于阶段性展示，但表述时不能夸大为“所有复杂工况都导致明显失败”。更稳妥的结论是：当前多模态三维检测模型在复杂工况下仍能输出检测框，但部分工况会造成检测可靠性下降，表现为平均置信度下降、高置信目标减少以及少量漏检。

其中，低光照和雾天样例影响相对较轻，适合作为辅助展示；运动模糊、图像噪声、点云稀疏和点云扰动对结果影响更明显，更适合作为说明复杂工况研究必要性的主要样例。

## 工况含义

- 运动模糊：车辆高速运动、目标快速移动、相机曝光时间较长或车身颠簸时，图像边缘会变模糊，目标轮廓更难识别。
- 图像噪声：夜晚弱光、相机高增益、镜头污染、雨雪灰尘或图像压缩传输时，画面会出现颗粒和杂色，小目标和远处目标更容易受影响。
- 点云稀疏：远距离目标、低线束激光雷达、雨雾灰尘遮挡、弱反射表面或传感器局部失效时，目标表面的雷达点会减少，三维结构不完整。
- 点云扰动：激光雷达测距误差、车辆振动、时间同步误差、外参标定误差、异常回波或设备漂移时，点云位置会出现偏移或抖动，三维框定位可靠性下降。

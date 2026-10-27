# 阶段 4 复杂工况样例生成报告

## 生成原则

每个生成样例都同时保存改变前 clean 数据和改变后 complex 数据，便于后续检测结果对比。

本阶段采用“多个原始样例，一一对应多种复杂工况”的方式。
每个原始样例最多生成一个复杂工况样例，不采用同一帧扩展多个工况的一对多方式。

## 样例数量

- 原始样例数量：`6`
- 可用复杂工况类型数量：`7`
- 建议最少原始样例数量：`5`
- 是否从阶段 3 自动补入 000008：`False`
- 是否基于已跑通样例生成多工况展示版：`False`

## 已生成样例

| 对比组 | 原始样例 | 复杂工况 | 改变前数据 | 改变后数据 | 点云点数变化 |
| --- | --- | --- | --- | --- | ---: |
| `000008_low_light` | `000008` | 弱光 (`low_light`) | `code\data\stage04_complex_conditions\paired_samples\000008_low_light\clean` | `code\data\stage04_complex_conditions\paired_samples\000008_low_light\complex` | 17238 -> 17238 |
| `000021_fog` | `000021` | 雾天 (`fog`) | `code\data\stage04_complex_conditions\paired_samples\000021_fog\clean` | `code\data\stage04_complex_conditions\paired_samples\000021_fog\complex` | 125260 -> 125260 |
| `000022_motion_blur` | `000022` | 运动模糊 (`motion_blur`) | `code\data\stage04_complex_conditions\paired_samples\000022_motion_blur\clean` | `code\data\stage04_complex_conditions\paired_samples\000022_motion_blur\complex` | 123219 -> 123219 |
| `000023_image_noise` | `000023` | 图像噪声 (`image_noise`) | `code\data\stage04_complex_conditions\paired_samples\000023_image_noise\clean` | `code\data\stage04_complex_conditions\paired_samples\000023_image_noise\complex` | 120412 -> 120412 |
| `000024_lidar_sparse` | `000024` | 点云稀疏 (`lidar_sparse`) | `code\data\stage04_complex_conditions\paired_samples\000024_lidar_sparse\clean` | `code\data\stage04_complex_conditions\paired_samples\000024_lidar_sparse\complex` | 126730 -> 57147 |
| `000025_lidar_jitter` | `000025` | 点云扰动 (`lidar_jitter`) | `code\data\stage04_complex_conditions\paired_samples\000025_lidar_jitter\clean` | `code\data\stage04_complex_conditions\paired_samples\000025_lidar_jitter\complex` | 115780 -> 115780 |

## 检测结果建议保存结构

服务器批量检测脚本会按照同样的一组一组方式保存结果：

```text
code/outputs/stage04_complex_conditions/mvxnet_comparison_results/
  对比组ID/
    clean/
    complex/
```

`clean/` 是改变前原始样例的检测结果，`complex/` 是改变后复杂工况样例的检测结果。

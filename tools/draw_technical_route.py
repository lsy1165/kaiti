from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "ppt" / "技术路线图_复杂工况三维目标检测.png"

S = 2
W, H = 1600 * S, 900 * S


def font(size, bold=False):
    candidates = [
        r"C:\Windows\Fonts\msyhbd.ttc" if bold else r"C:\Windows\Fonts\msyh.ttc",
        r"C:\Windows\Fonts\simhei.ttf",
        r"C:\Windows\Fonts\simsun.ttc",
    ]
    for path in candidates:
        p = Path(path)
        if p.exists():
            return ImageFont.truetype(str(p), size * S)
    return ImageFont.load_default()


F_SECTION = font(27, True)
F_BOX_TITLE = font(23, True)
F_BOX = font(19)
F_SMALL = font(17)
F_TECH = font(14, True)
F_TINY = font(13, True)
F_NOTE = font(18, True)


def xy(v):
    return tuple(int(a * S) for a in v)


def box(draw, rect, fill, outline, width=3, radius=6):
    draw.rounded_rectangle(xy(rect), radius=radius * S, fill=fill, outline=outline, width=width * S)


def text_center(draw, center, text, fnt, fill="#111827"):
    draw.text(xy(center), text, font=fnt, fill=fill, anchor="mm")


def arrow(draw, start, end, color, width=3):
    x1, y1 = xy(start)
    x2, y2 = xy(end)
    draw.line((x1, y1, x2, y2), fill=color, width=width * S)
    import math

    ang = math.atan2(y2 - y1, x2 - x1)
    length = 14 * S
    spread = 0.42
    p1 = (x2 - length * math.cos(ang - spread), y2 - length * math.sin(ang - spread))
    p2 = (x2 - length * math.cos(ang + spread), y2 - length * math.sin(ang + spread))
    draw.polygon([(x2, y2), p1, p2], fill=color)


def poly_arrow(draw, points, color, width=3):
    scaled = [xy(p) for p in points]
    draw.line(scaled, fill=color, width=width * S, joint="curve")
    arrow(draw, points[-2], points[-1], color, width)


def dashed_line(draw, start, end, color, width=2, dash=9, gap=7):
    import math

    x1, y1 = xy(start)
    x2, y2 = xy(end)
    total = math.hypot(x2 - x1, y2 - y1)
    if total == 0:
        return
    ux, uy = (x2 - x1) / total, (y2 - y1) / total
    pos = 0
    while pos < total:
        end_pos = min(pos + dash * S, total)
        sx, sy = x1 + ux * pos, y1 + uy * pos
        ex, ey = x1 + ux * end_pos, y1 + uy * end_pos
        draw.line((sx, sy, ex, ey), fill=color, width=width * S)
        pos += (dash + gap) * S


def dashed_polyline(draw, points, color, width=2, dash=9, gap=7):
    for a, b in zip(points, points[1:]):
        dashed_line(draw, a, b, color, width, dash, gap)
    arrow(draw, points[-2], points[-1], color, width)


def dashed_rect(draw, rect, outline, width=2, radius=5, dash=9, gap=7, fill="#ffffff"):
    if fill:
        draw.rounded_rectangle(xy(rect), radius=radius * S, fill=fill)
    x1, y1, x2, y2 = rect
    dashed_line(draw, (x1 + radius, y1), (x2 - radius, y1), outline, width, dash, gap)
    dashed_line(draw, (x2, y1 + radius), (x2, y2 - radius), outline, width, dash, gap)
    dashed_line(draw, (x2 - radius, y2), (x1 + radius, y2), outline, width, dash, gap)
    dashed_line(draw, (x1, y2 - radius), (x1, y1 + radius), outline, width, dash, gap)


img = Image.new("RGB", (W, H), "white")
d = ImageDraw.Draw(img)

purple = "#8b5cf6"
blue = "#2563eb"
green = "#16a34a"
orange = "#f59e0b"
teal = "#0891b2"
sky = "#0ea5e9"
muted = "#374151"

# Left panel: previous work
box(d, (54, 128, 384, 828), "#fbf7ff", purple, 4, 18)
box(d, (102, 98, 278, 156), purple, purple, 0, 6)
text_center(d, (190, 127), "前期工作", F_SECTION, "white")

left_items = [
    ((93, 188, 345, 252), "二维目标检测复现", "YOLOv8：图像二维框检测"),
    ((93, 290, 345, 354), "点云三维检测复现", "PointPillars：BEV 三维框"),
    ((93, 392, 345, 462), "多模态三维检测复现", "MVX-Net：图像 + 点云融合"),
]
for rect, title, subtitle in left_items:
    box(d, rect, "#ffffff", purple, 3, 5)
    cx = (rect[0] + rect[2]) / 2
    text_center(d, (cx, rect[1] + 26), title, F_BOX_TITLE)
    text_center(d, (cx, rect[1] + 51), subtitle, F_SMALL, "#4b5563")

arrow(d, (219, 252), (219, 287), purple, 3)
arrow(d, (219, 354), (219, 389), purple, 3)
arrow(d, (219, 462), (219, 498), purple, 3)

box(d, (78, 502, 360, 606), "#ffffff", purple, 3, 6)
text_center(d, (219, 531), "复杂工况样本构造", F_BOX_TITLE)
text_center(d, (219, 560), "弱光 / 雾天 / 模糊 / 噪声", F_SMALL, "#4b5563")
text_center(d, (219, 587), "点云稀疏 / 点云扰动", F_SMALL, "#4b5563")

arrow(d, (219, 606), (219, 642), purple, 3)

box(d, (78, 646, 360, 758), "#fff7ed", orange, 3, 6)
text_center(d, (219, 675), "Clean / Complex 对比", F_BOX_TITLE)
text_center(d, (219, 706), "置信度下降、漏检", F_SMALL, "#4b5563")
text_center(d, (219, 733), "三维框定位不稳定", F_SMALL, "#4b5563")

# Right panel: future work
right_panel = (500, 128, 1368, 828)
arrow(d, (384, 470), (500, 470), blue, 4)
box(d, right_panel, "#f8fbff", blue, 4, 18)
box(d, (552, 98, 792, 156), blue, blue, 0, 6)
text_center(d, (672, 127), "后续研究内容", F_SECTION, "white")

box(d, (560, 184, 1318, 264), "#ffffff", sky, 3, 8)
text_center(d, (939, 213), "面向六类复杂工况的退化感知建模", F_BOX_TITLE)
text_center(d, (939, 242), "弱光、雾天、运动模糊、图像噪声、点云稀疏、点云扰动", F_SMALL, "#4b5563")

# Core flow
box(d, (580, 320, 790, 410), "#ffffff", blue, 3, 6)
text_center(d, (685, 354), "图像分支", F_BOX_TITLE)
text_center(d, (685, 383), "语义特征提取", F_BOX, muted)

box(d, (580, 490, 790, 580), "#ffffff", green, 3, 6)
text_center(d, (685, 524), "点云分支", F_BOX_TITLE)
text_center(d, (685, 553), "几何特征提取", F_BOX, muted)

box(d, (850, 310, 1070, 430), "#eff6ff", blue, 3, 6)
text_center(d, (960, 343), "图像退化评估", F_BOX_TITLE)
text_center(d, (960, 374), "亮度 / 对比度 / 模糊", F_SMALL, "#4b5563")
text_center(d, (960, 401), "噪声强度 / 雾化程度", F_SMALL, "#4b5563")

box(d, (850, 480, 1070, 600), "#f0fdf4", green, 3, 6)
text_center(d, (960, 513), "点云退化评估", F_BOX_TITLE)
text_center(d, (960, 544), "点云密度 / 有效点数量", F_SMALL, "#4b5563")
text_center(d, (960, 571), "几何完整性 / 扰动程度", F_SMALL, "#4b5563")

box(d, (1130, 390, 1285, 530), "#fff7ed", orange, 4, 8)
text_center(d, (1207, 433), "可靠性权重", F_BOX_TITLE)
text_center(d, (1207, 464), "生成模块", F_BOX_TITLE)
text_center(d, (1207, 498), "动态调节", F_SMALL, "#4b5563")

arrow(d, (790, 365), (837, 365), blue, 3)
arrow(d, (790, 535), (837, 535), green, 3)
poly_arrow(d, [(1070, 370), (1100, 400), (1120, 430)], orange, 3)
poly_arrow(d, [(1070, 540), (1100, 505), (1120, 485)], orange, 3)

box(d, (645, 660, 895, 748), "#ffffff", purple, 3, 6)
text_center(d, (770, 695), "图像特征 + 点云特征", F_BOX_TITLE)
text_center(d, (770, 724), "按可靠性自适应融合", F_BOX, muted)

box(d, (960, 660, 1160, 748), "#ffffff", teal, 3, 6)
text_center(d, (1060, 695), "三维目标检测", F_BOX_TITLE)
text_center(d, (1060, 724), "位置 / 尺寸 / 朝向", F_BOX, muted)

box(d, (1220, 660, 1340, 748), "#ecfdf5", green, 3, 6)
text_center(d, (1280, 695), "稳定性提升", F_BOX_TITLE)
text_center(d, (1280, 724), "减少退化干扰", F_SMALL, "#4b5563")

poly_arrow(d, [(1207, 530), (1207, 615), (895, 695)], orange, 3)
arrow(d, (895, 704), (947, 704), purple, 3)
arrow(d, (1160, 704), (1207, 704), green, 3)

poly_arrow(d, [(580, 365), (540, 365), (540, 704), (632, 704)], blue, 3)
arrow(d, (685, 580), (685, 660), green, 3)

box(d, (560, 780, 1318, 812), "#fef3c7", orange, 2, 6)
text_center(d, (939, 797), "核心目标：降低退化模态对融合结果的干扰，提升复杂工况下三维检测可靠性", F_NOTE, "#7c2d12")

# External technology boxes
dashed_rect(d, (840, 18, 1518, 90), sky, 2, 5)
text_center(d, (1179, 38), "基础检测与融合框架", F_TECH, "#0369a1")
for rect, label in [
    ((865, 54, 1078, 80), "MMDetection3D + MVX-Net"),
    ((1100, 54, 1280, 80), "参考：BEVFusion"),
    ((1302, 54, 1495, 80), "参考：TransFusion"),
]:
    box(d, rect, "#ffffff", "#111827", 1, 2)
    text_center(d, ((rect[0] + rect[2]) / 2, 67), label, F_TECH)
dashed_polyline(d, [(672, 98), (672, 60), (840, 60)], sky, 2)

dashed_rect(d, (1390, 270, 1580, 382), blue, 2, 5)
text_center(d, (1485, 292), "图像质量评估技术", F_TECH, "#1d4ed8")
text_center(d, (1485, 318), "OpenCV", F_TECH)
text_center(d, (1485, 342), "HSV亮度 / 对比度", F_TINY)
text_center(d, (1485, 366), "Laplacian模糊 / 噪声估计", F_TINY)
dashed_polyline(d, [(1070, 370), (1380, 370), (1390, 326)], blue, 2)

dashed_rect(d, (1390, 430, 1580, 560), orange, 2, 5)
text_center(d, (1485, 454), "权重与融合技术", F_TECH, "#c2410c")
text_center(d, (1485, 481), "MLP + Softmax", F_TECH)
text_center(d, (1485, 505), "可靠性权重", F_TINY)
text_center(d, (1485, 529), "门控加权 / 注意力", F_TINY)
text_center(d, (1485, 547), "加权Concat融合", F_TINY)
dashed_polyline(d, [(1285, 460), (1380, 460), (1390, 495)], orange, 2)

dashed_rect(d, (1390, 620, 1580, 742), green, 2, 5)
text_center(d, (1485, 642), "点云质量评估技术", F_TECH, "#15803d")
text_center(d, (1485, 668), "Open3D / PCL", F_TECH)
text_center(d, (1485, 692), "点密度 / 有效点", F_TINY)
text_center(d, (1485, 716), "KNN距离方差 / BEV占用", F_TINY)
dashed_polyline(d, [(1070, 540), (1345, 540), (1345, 681), (1390, 681)], green, 2)

OUT.parent.mkdir(parents=True, exist_ok=True)
img.save(OUT)
print(OUT)

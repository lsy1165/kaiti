from pathlib import Path
import math
import random

from PIL import Image, ImageDraw, ImageFont


OUT_DIR = Path(r"E:\kaiti\ppt\原理示意图")
W, H = 3200, 1800

BLUE = "#2563EB"
BLUE_D = "#1E40AF"
BLUE_L = "#EFF6FF"
GREEN = "#16A34A"
GREEN_D = "#15803D"
GREEN_L = "#F0FDF4"
ORANGE = "#F59E0B"
ORANGE_D = "#D97706"
ORANGE_L = "#FFF7ED"
PURPLE = "#8B5CF6"
PURPLE_L = "#F5F3FF"
CYAN = "#0891B2"
CYAN_L = "#ECFEFF"
GRAY = "#64748B"
INK = "#0F172A"
SUB = "#475569"
LINE = "#CBD5E1"
BG = "#F8FAFC"
WHITE = "#FFFFFF"


def font(size, bold=False):
    candidates = [
        r"C:\Windows\Fonts\msyhbd.ttc" if bold else r"C:\Windows\Fonts\msyh.ttc",
        r"C:\Windows\Fonts\simhei.ttf",
        r"C:\Windows\Fonts\simsun.ttc",
        r"C:\Windows\Fonts\arial.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


F = {
    "title": font(72, True),
    "subtitle": font(34),
    "section": font(42, True),
    "body": font(30),
    "small": font(24),
    "tiny": font(21),
    "num": font(32, True),
}


def text_size(draw, text, fnt):
    box = draw.textbbox((0, 0), text, font=fnt)
    return box[2] - box[0], box[3] - box[1]


def wrap_text(draw, text, fnt, max_width):
    lines = []
    current = ""
    for ch in text:
        test = current + ch
        if text_size(draw, test, fnt)[0] <= max_width or not current:
            current = test
        else:
            lines.append(current)
            current = ch
    if current:
        lines.append(current)
    return lines


def center_text(draw, box, text, fnt, fill=INK, spacing=8):
    x1, y1, x2, y2 = box
    lines = []
    for part in str(text).split("\n"):
        lines.extend(wrap_text(draw, part, fnt, x2 - x1 - 40))
    heights = [text_size(draw, line, fnt)[1] for line in lines]
    total = sum(heights) + spacing * (len(lines) - 1)
    y = y1 + (y2 - y1 - total) / 2
    for line, hh in zip(lines, heights):
        ww, _ = text_size(draw, line, fnt)
        draw.text((x1 + (x2 - x1 - ww) / 2, y), line, font=fnt, fill=fill)
        y += hh + spacing


def left_text(draw, xy, text, fnt, fill=INK, max_width=None, spacing=8):
    x, y = xy
    lines = []
    for part in str(text).split("\n"):
        if max_width:
            lines.extend(wrap_text(draw, part, fnt, max_width))
        else:
            lines.append(part)
    for line in lines:
        draw.text((x, y), line, font=fnt, fill=fill)
        y += text_size(draw, line, fnt)[1] + spacing
    return y


def rounded(draw, box, radius=24, fill=WHITE, outline=LINE, width=4):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def shadow_box(draw, box, radius=26, fill=WHITE, outline=LINE, width=4, shadow="#E2E8F0"):
    x1, y1, x2, y2 = box
    draw.rounded_rectangle((x1 + 10, y1 + 12, x2 + 10, y2 + 12), radius=radius, fill=shadow)
    rounded(draw, box, radius, fill, outline, width)


def arrow(draw, start, end, color=BLUE, width=8, head=28):
    x1, y1 = start
    x2, y2 = end
    draw.line((x1, y1, x2, y2), fill=color, width=width)
    angle = math.atan2(y2 - y1, x2 - x1)
    p1 = (x2 - head * math.cos(angle - math.pi / 6), y2 - head * math.sin(angle - math.pi / 6))
    p2 = (x2 - head * math.cos(angle + math.pi / 6), y2 - head * math.sin(angle + math.pi / 6))
    draw.polygon([(x2, y2), p1, p2], fill=color)


def dashed_arrow(draw, start, end, color=GRAY, width=5, dash=28, gap=18, head=24):
    x1, y1 = start
    x2, y2 = end
    length = math.hypot(x2 - x1, y2 - y1)
    if length == 0:
        return
    ux, uy = (x2 - x1) / length, (y2 - y1) / length
    pos = 0
    while pos < length - head:
        seg = min(dash, length - head - pos)
        a = (x1 + ux * pos, y1 + uy * pos)
        b = (x1 + ux * (pos + seg), y1 + uy * (pos + seg))
        draw.line((*a, *b), fill=color, width=width)
        pos += dash + gap
    angle = math.atan2(y2 - y1, x2 - x1)
    p1 = (x2 - head * math.cos(angle - math.pi / 6), y2 - head * math.sin(angle - math.pi / 6))
    p2 = (x2 - head * math.cos(angle + math.pi / 6), y2 - head * math.sin(angle + math.pi / 6))
    draw.polygon([(x2, y2), p1, p2], fill=color)


def canvas(title, subtitle):
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)
    draw.rectangle((0, 0, W, 190), fill="#EAF2FF")
    draw.rectangle((0, 190, W, 198), fill=BLUE)
    draw.text((115, 30), title, font=F["title"], fill=INK)
    draw.text((115, 118), subtitle, font=F["subtitle"], fill=SUB)
    return img, draw


def module(draw, box, title, body="", color=BLUE, fill=WHITE, title_color=INK, body_color=SUB):
    shadow_box(draw, box, 28, fill, color, 5)
    x1, y1, x2, y2 = box
    draw.text((x1 + 34, y1 + 28), title, font=F["section"], fill=title_color)
    if body:
        left_text(draw, (x1 + 34, y1 + 92), body, F["body"], body_color, x2 - x1 - 68, 10)


def badge(draw, xy, text, fill, outline=None):
    x, y = xy
    w, h = text_size(draw, text, F["small"])
    box = (x, y, x + w + 34, y + h + 22)
    draw.rounded_rectangle(box, radius=18, fill=fill, outline=outline or fill, width=3)
    draw.text((x + 17, y + 9), text, font=F["small"], fill=INK)
    return box


def draw_road_scene(draw, box, boxes=True):
    x1, y1, x2, y2 = box
    bw, bh = x2 - x1, y2 - y1
    rounded(draw, box, 26, "#DBEAFE", BLUE, 5)
    draw.rectangle((x1 + 20, y1 + 28, x2 - 20, y2 - 20), fill="#BFDBFE")
    horizon = y1 + bh * 0.36
    road_bottom = y2 - 35
    road_left_top = x1 + bw * 0.50
    road_right_top = x1 + bw * 0.50
    draw.polygon([(x1 + 20, road_bottom), (road_left_top, horizon), (road_right_top, horizon), (x2 - 20, road_bottom)], fill="#334155")
    draw.polygon([(x1 + 20, road_bottom), (road_left_top, horizon), (x1 + 20, horizon)], fill="#94A3B8")
    draw.polygon([(x2 - 20, road_bottom), (road_right_top, horizon), (x2 - 20, horizon)], fill="#94A3B8")
    for k in range(5):
        yy = y2 - bh * (0.11 + k * 0.10)
        cx = x1 + bw * (0.50 + k * 0.018)
        draw.rectangle((cx - bw * 0.018, yy, cx + bw * 0.018, yy + bh * 0.055), fill="#F8FAFC")
    cars = [
        (x1 + bw * 0.22, y1 + bh * 0.66, bw * 0.17, bh * 0.105, "#F97316"),
        (x1 + bw * 0.50, y1 + bh * 0.56, bw * 0.13, bh * 0.085, "#22C55E"),
        (x1 + bw * 0.76, y1 + bh * 0.63, bw * 0.15, bh * 0.095, "#A855F7"),
    ]
    for cx, cy, cw, ch, color in cars:
        radius = max(8, int(ch * 0.22))
        lw = max(2, int(bw * 0.004))
        draw.rounded_rectangle((cx, cy, cx + cw, cy + ch), radius=radius, fill=color, outline=INK, width=lw)
        draw.rectangle((cx + cw * 0.26, cy - ch * 0.32, cx + cw * 0.74, cy + ch * 0.12), fill="#E0F2FE", outline=INK, width=lw)
        wr = max(5, int(ch * 0.20))
        draw.ellipse((cx + cw * 0.16, cy + ch * 0.78, cx + cw * 0.16 + wr * 2, cy + ch * 0.78 + wr * 2), fill=INK)
        draw.ellipse((cx + cw * 0.70, cy + ch * 0.78, cx + cw * 0.70 + wr * 2, cy + ch * 0.78 + wr * 2), fill=INK)
        if boxes:
            draw.rectangle((cx - bw * 0.016, cy - ch * 0.45, cx + cw + bw * 0.016, cy + ch * 1.32), outline="#FACC15", width=max(4, int(bw * 0.006)))
    # pedestrian
    if bw > 560:
        px, py = x1 + bw * 0.91, y1 + bh * 0.59
        head = bh * 0.045
        linew = max(4, int(bw * 0.007))
        draw.ellipse((px, py, px + head, py + head), fill="#FDE68A", outline=INK, width=max(2, linew // 2))
        draw.line((px + head / 2, py + head, px + head / 2, py + head * 2.8), fill=INK, width=linew)
        draw.line((px + head / 2, py + head * 1.6, px - head * 0.5, py + head * 2.1), fill=INK, width=max(3, linew - 1))
        draw.line((px + head / 2, py + head * 1.6, px + head * 1.5, py + head * 2.1), fill=INK, width=max(3, linew - 1))
        draw.line((px + head / 2, py + head * 2.8, px - head * 0.3, py + head * 4.0), fill=INK, width=max(3, linew - 1))
        draw.line((px + head / 2, py + head * 2.8, px + head * 1.35, py + head * 4.0), fill=INK, width=max(3, linew - 1))
        if boxes:
            draw.rectangle((px - head * 0.7, py - head * 0.2, px + head * 1.8, py + head * 4.25), outline="#FACC15", width=max(4, int(bw * 0.006)))
    if bw > 430:
        draw.text((x1 + 35, y1 + 36), "道路图像示意", font=F["small"], fill=BLUE_D)


def draw_feature_pyramid(draw, origin, color=BLUE):
    x, y = origin
    sizes = [(250, 92), (210, 78), (170, 64), (130, 52)]
    for i, (ww, hh) in enumerate(sizes):
        bx = x + i * 34
        by = y + i * 80
        draw.rounded_rectangle((bx, by, bx + ww, by + hh), radius=12, fill="#DBEAFE", outline=color, width=4)
        for k in range(6):
            draw.line((bx + 20, by + 18 + k * 11, bx + ww - 20, by + 18 + k * 11), fill="#93C5FD", width=3)
        draw.text((bx + ww + 18, by + 18), f"P{i+2}", font=F["small"], fill=color)


def draw_bev_grid(draw, box, color=GREEN, boxes=True):
    x1, y1, x2, y2 = box
    bw, bh = x2 - x1, y2 - y1
    rounded(draw, box, 24, "#ECFDF5", color, 5)
    step = max(28, int(min(bw, bh) / 7))
    for x in range(x1 + 28, x2 - 28, step):
        draw.line((x, y1 + 30, x, y2 - 30), fill="#BBF7D0", width=2)
    for y in range(y1 + 30, y2 - 30, step):
        draw.line((x1 + 28, y, x2 - 28, y), fill="#BBF7D0", width=2)
    rng = random.Random(7)
    n_points = max(90, int(bw * bh / 1700))
    for _ in range(n_points):
        px = rng.randint(x1 + 55, x2 - 55)
        py = rng.randint(y1 + 55, y2 - 55)
        r = rng.choice([3, 4, 5])
        draw.ellipse((px - r, py - r, px + r, py + r), fill=color)
    if boxes:
        specs = [
            (0.30, 0.43, 0.25, 0.12, -10),
            (0.60, 0.62, 0.29, 0.13, 16),
            (0.77, 0.36, 0.23, 0.11, 4),
        ]
        for rx, ry, rw, rh, ang in specs:
            cx, cy, ww, hh = x1 + bw * rx, y1 + bh * ry, bw * rw, bh * rh
            rotated_rect(draw, (cx, cy), ww, hh, ang, "#F59E0B")
    if bw > 300:
        draw.text((x1 + 28, y1 + 28), "BEV 鸟瞰视角", font=F["small"], fill=GREEN_D)


def rotated_rect(draw, center, w, h, angle, outline, width=6, fill=None):
    cx, cy = center
    a = math.radians(angle)
    pts = []
    for dx, dy in [(-w/2, -h/2), (w/2, -h/2), (w/2, h/2), (-w/2, h/2)]:
        pts.append((cx + dx * math.cos(a) - dy * math.sin(a), cy + dx * math.sin(a) + dy * math.cos(a)))
    if fill:
        draw.polygon(pts, fill=fill)
    draw.line(pts + [pts[0]], fill=outline, width=width)
    # heading mark
    hx = cx + (w/2 + 20) * math.cos(a)
    hy = cy + (w/2 + 20) * math.sin(a)
    arrow(draw, (cx, cy), (hx, hy), outline, max(3, width - 2), 18)


def draw_point_cloud(draw, box):
    x1, y1, x2, y2 = box
    rounded(draw, box, 24, "#F8FAFC", GREEN, 5)
    rng = random.Random(11)
    origin = (x1 + 85, y2 - 90)
    for ray in range(9):
        angle = -55 + ray * 13
        length = rng.randint(360, 620)
        ex = origin[0] + math.cos(math.radians(angle)) * length
        ey = origin[1] + math.sin(math.radians(angle)) * length
        draw.line((origin[0], origin[1], ex, ey), fill="#DCFCE7", width=3)
    for _ in range(390):
        px = rng.randint(x1 + 80, x2 - 80)
        py = rng.randint(y1 + 75, y2 - 75)
        if rng.random() < 0.25:
            px += rng.randint(-20, 20)
            py += rng.randint(-12, 12)
        r = rng.choice([2, 3, 4])
        draw.ellipse((px - r, py - r, px + r, py + r), fill=GREEN)
    draw.polygon([(origin[0]-28, origin[1]+18), (origin[0]+32, origin[1]+18), (origin[0]+45, origin[1]+52), (origin[0]-45, origin[1]+52)], fill="#0F172A")
    draw.text((x1 + 32, y1 + 32), "激光雷达点云示意", font=F["small"], fill=GREEN_D)


def diagram_2d():
    img, draw = canvas(
        "二维目标检测原理",
        "输入 RGB 图像，提取多尺度语义特征，在图像平面输出类别、置信度和 2D 边界框",
    )
    draw_road_scene(draw, (120, 265, 1150, 1055), boxes=True)
    badge(draw, (150, 1098), "输出：类别 + 置信度 + 2D 框", "#FEF3C7", ORANGE)

    y = 360
    module(draw, (1300, y, 1790, y + 250), "1  特征提取", "Backbone 提取纹理、边缘和语义信息\nFPN 形成多尺度特征，兼顾近处大目标与远处小目标", BLUE, BLUE_L)
    draw_feature_pyramid(draw, (1880, y + 12), BLUE)
    module(draw, (1300, 760, 1790, 990), "2  检测预测", "检测头预测每个候选位置的类别概率、目标置信度和边界框坐标", BLUE, BLUE_L)
    module(draw, (2025, 760, 2515, 990), "3  筛选输出", "按置信度阈值和 NMS 去除重复框，保留最终检测结果", ORANGE, ORANGE_L)
    draw_road_scene(draw, (2650, 545, 3090, 1030), boxes=True)

    arrow(draw, (1150, 660), (1300, 485), BLUE, 9, 34)
    arrow(draw, (1790, 880), (2025, 880), BLUE, 9, 34)
    arrow(draw, (2515, 880), (2650, 790), ORANGE, 9, 34)

    rounded(draw, (1300, 1180, 3090, 1585), 30, WHITE, LINE, 4)
    draw.text((1350, 1230), "讲解要点", font=F["section"], fill=INK)
    left_text(draw, (1350, 1305),
              "适合说明“目标在哪里、是什么”。典型方法包括两阶段检测器（如 Faster R-CNN）和单阶段检测器（如 YOLO）。\n"
              "局限在于输出位于图像平面，不能直接给出真实距离、三维尺寸和空间朝向。",
              F["body"], SUB, 1630, 14)
    for x, label, color in [(145, "图像平面", BLUE), (370, "多尺度特征", BLUE), (640, "候选框筛选", ORANGE), (905, "二维输出", ORANGE)]:
        badge(draw, (x, 1450), label, "#FFFFFF", color)
    img.save(OUT_DIR / "01_二维目标检测原理.png")


def diagram_lidar():
    img, draw = canvas(
        "点云单模态三维目标检测原理",
        "以 PointPillars 类方法为例：将稀疏点云组织成柱体/体素，编码为 BEV 伪图像后预测三维框",
    )
    draw_point_cloud(draw, (120, 275, 760, 870))
    module(draw, (910, 300, 1380, 520), "1  点云划分", "按 x-y 平面网格划分柱体\n限制非空柱体和每柱点数", GREEN, GREEN_L)
    # pillar grid icon
    gx1, gy1, gx2, gy2 = 1000, 600, 1320, 900
    rounded(draw, (gx1, gy1, gx2, gy2), 22, "#F0FDF4", GREEN, 5)
    for i in range(7):
        draw.line((gx1 + 30 + i * 42, gy1 + 32, gx1 + 30 + i * 42, gy2 - 32), fill="#86EFAC", width=3)
        draw.line((gx1 + 30, gy1 + 32 + i * 36, gx2 - 30, gy1 + 32 + i * 36), fill="#86EFAC", width=3)
    rng = random.Random(5)
    for _ in range(45):
        px = rng.randint(gx1 + 45, gx2 - 45)
        py = rng.randint(gy1 + 45, gy2 - 45)
        draw.rectangle((px - 9, py - 9, px + 9, py + 9), fill=GREEN)
    center_text(draw, (gx1 + 20, gy2 - 70, gx2 - 20, gy2 - 20), "Pillar / Voxel", F["small"], GREEN_D)

    module(draw, (1510, 300, 2035, 520), "2  柱体特征编码", "PointNet / VFE 学习每个柱体的局部几何特征\n再散射成 C×H×W 伪图像", GREEN, GREEN_L)
    draw_bev_grid(draw, (1540, 610, 2010, 990), GREEN, boxes=False)

    module(draw, (2180, 300, 2640, 520), "3  BEV Backbone", "使用 2D CNN 在鸟瞰图上聚合上下文\n得到更高层空间特征", BLUE, BLUE_L)
    draw_bev_grid(draw, (2200, 610, 2660, 990), BLUE, boxes=False)

    module(draw, (2785, 430, 3120, 760), "4  3D 检测头", "分类\n置信度\n位置 / 尺寸 / 朝向", ORANGE, ORANGE_L)
    draw_bev_grid(draw, (2785, 930, 3120, 1285), ORANGE, boxes=True)

    arrow(draw, (760, 575), (910, 410), GREEN, 9, 34)
    arrow(draw, (1380, 410), (1510, 410), GREEN, 9, 34)
    arrow(draw, (2035, 410), (2180, 410), BLUE, 9, 34)
    arrow(draw, (2640, 570), (2785, 575), ORANGE, 9, 34)

    rounded(draw, (120, 1135, 2640, 1585), 30, WHITE, LINE, 4)
    draw.text((170, 1185), "讲解要点", font=F["section"], fill=INK)
    left_text(draw, (170, 1262),
              "点云检测直接利用空间几何信息，能够预测三维位置、尺寸和朝向。PointPillars 的关键是把无序稀疏点云转换成规则 BEV 伪图像，使后续可以使用高效的 2D 卷积检测结构。\n"
              "局限在于远距离、遮挡、点云稀疏或坐标扰动会破坏几何结构，影响三维框定位稳定性。",
              F["body"], SUB, 2360, 14)
    badge(draw, (120, 1620), "三维输出：x / y / z + l / w / h + yaw", "#FFFFFF", ORANGE)
    badge(draw, (780, 1620), "优势：空间定位强", "#FFFFFF", GREEN)
    badge(draw, (1170, 1620), "风险：点云稀疏与扰动", "#FFFFFF", GREEN)
    img.save(OUT_DIR / "02_点云三维检测原理.png")


def diagram_fusion():
    img, draw = canvas(
        "图像-激光雷达多模态三维检测原理",
        "图像提供语义信息，点云提供几何信息，通过标定投影或 BEV 对齐后融合并输出三维检测框",
    )
    draw_road_scene(draw, (120, 255, 790, 700), boxes=False)
    draw_point_cloud(draw, (120, 930, 790, 1375))
    module(draw, (930, 270, 1420, 520), "图像分支", "CNN / FPN 提取颜色、纹理、类别语义\n复杂工况：弱光、雾天、模糊、噪声", BLUE, BLUE_L)
    module(draw, (930, 960, 1420, 1210), "点云分支", "Voxel / Pillar 编码空间几何与 BEV 特征\n复杂工况：稀疏、缺失、扰动", GREEN, GREEN_L)

    module(draw, (1620, 560, 2145, 840), "跨模态对齐", "利用内外参标定进行点到图像投影\n或将两路特征统一到 BEV 空间", CYAN, CYAN_L)
    module(draw, (1620, 995, 2145, 1285), "模态质量评估", "图像：亮度 / 对比度 / 模糊 / 噪声\n点云：密度 / 有效点 / KNN 方差 / BEV 占用", PURPLE, PURPLE_L)
    module(draw, (2320, 695, 2820, 1015), "融合与权重调节", "Concat / 门控加权 / 注意力\n按可靠性调整语义特征与几何特征贡献", ORANGE, ORANGE_L)
    draw_bev_grid(draw, (2365, 1130, 2875, 1515), ORANGE, boxes=True)

    module(draw, (2950, 740, 3150, 1020), "输出", "类别\n置信度\n三维框", BLUE, "#F0F9FF")

    arrow(draw, (790, 480), (930, 390), BLUE, 9, 34)
    arrow(draw, (790, 1160), (930, 1085), GREEN, 9, 34)
    arrow(draw, (1420, 395), (1620, 650), BLUE, 9, 34)
    arrow(draw, (1420, 1085), (1620, 740), GREEN, 9, 34)
    dashed_arrow(draw, (1420, 520), (1620, 1060), BLUE, 6, 28, 20, 28)
    dashed_arrow(draw, (1420, 960), (1620, 1190), GREEN, 6, 28, 20, 28)
    arrow(draw, (2145, 700), (2320, 800), CYAN, 9, 34)
    arrow(draw, (2145, 1120), (2320, 910), PURPLE, 9, 34)
    arrow(draw, (2820, 860), (2950, 880), ORANGE, 9, 34)

    rounded(draw, (120, 1485, 2190, 1660), 26, WHITE, LINE, 4)
    draw.text((165, 1530), "讲解要点", font=F["section"], fill=INK)
    left_text(draw, (420, 1530),
              "多模态检测的核心不是简单叠加两路输入，而是先解决“对齐”，再决定“融合”。复杂工况下，一路模态退化时需要降低其负面影响。",
              F["body"], SUB, 1700, 10)
    badge(draw, (120, 1700), "语义信息：图像强", "#FFFFFF", BLUE)
    badge(draw, (530, 1700), "几何信息：点云强", "#FFFFFF", GREEN)
    badge(draw, (950, 1700), "研究切入：可靠性权重", "#FFFFFF", ORANGE)
    img.save(OUT_DIR / "03_多模态融合三维检测原理.png")


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    diagram_2d()
    diagram_lidar()
    diagram_fusion()
    print(f"saved to {OUT_DIR}")


if __name__ == "__main__":
    main()

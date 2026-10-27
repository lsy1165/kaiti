from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "ppt" / "复杂工况三维目标检测方法结构示意图.png"

S = 2
W, H = 1600 * S, 820 * S


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


F_TITLE = font(34, True)
F_BOX = font(22, True)
F_TEXT = font(18)
F_SMALL = font(15)
F_TINY = font(14)


def xy(values):
    return tuple(int(v * S) for v in values)


def box(draw, rect, fill, outline, width=3, radius=8):
    draw.rounded_rectangle(xy(rect), radius=radius * S, fill=fill, outline=outline, width=width * S)


def label(draw, pos, text, fnt, fill="#111827", anchor="mm"):
    draw.text(xy(pos), text, font=fnt, fill=fill, anchor=anchor)


def arrow(draw, start, end, color="#374151", width=3):
    import math

    x1, y1 = xy(start)
    x2, y2 = xy(end)
    draw.line((x1, y1, x2, y2), fill=color, width=width * S)
    angle = math.atan2(y2 - y1, x2 - x1)
    length = 13 * S
    spread = 0.42
    p1 = (x2 - length * math.cos(angle - spread), y2 - length * math.sin(angle - spread))
    p2 = (x2 - length * math.cos(angle + spread), y2 - length * math.sin(angle + spread))
    draw.polygon([(x2, y2), p1, p2], fill=color)


def poly_arrow(draw, points, color="#374151", width=3):
    draw.line([xy(p) for p in points], fill=color, width=width * S, joint="curve")
    arrow(draw, points[-2], points[-1], color, width)


img = Image.new("RGB", (W, H), "white")
d = ImageDraw.Draw(img)

blue = "#2563eb"
green = "#16a34a"
orange = "#f59e0b"
purple = "#8b5cf6"
teal = "#0891b2"
gray = "#374151"
dark = "#111827"

label(d, (800, 54), "复杂工况下三维目标检测方法结构示意图", F_TITLE, dark)

# Inputs
box(d, (55, 165, 205, 225), "#ffffff", blue, 3, 8)
label(d, (130, 195), "相机图像", F_BOX)
label(d, (130, 252), "弱光 / 雾天 / 模糊 / 噪声", F_SMALL, "#4b5563")

box(d, (55, 525, 205, 585), "#ffffff", green, 3, 8)
label(d, (130, 555), "激光雷达点云", F_BOX)
label(d, (130, 612), "点云稀疏 / 点云扰动", F_SMALL, "#4b5563")

# Feature and quality branches
box(d, (300, 135, 520, 235), "#eff6ff", blue, 3, 8)
label(d, (410, 172), "图像特征提取", F_BOX)
label(d, (410, 205), "CNN / FPN", F_TEXT, gray)

box(d, (300, 275, 520, 385), "#ffffff", blue, 3, 8)
label(d, (410, 309), "图像质量评估", F_BOX)
label(d, (410, 340), "HSV亮度 / 对比度", F_SMALL, gray)
label(d, (410, 365), "Laplacian模糊 / 噪声", F_SMALL, gray)

box(d, (300, 405, 520, 515), "#ffffff", green, 3, 8)
label(d, (410, 439), "点云质量评估", F_BOX)
label(d, (410, 470), "点密度 / 有效点", F_SMALL, gray)
label(d, (410, 495), "KNN距离方差 / BEV占用", F_SMALL, gray)

box(d, (300, 555, 520, 655), "#f0fdf4", green, 3, 8)
label(d, (410, 592), "点云特征提取", F_BOX)
label(d, (410, 625), "体素化 / BEV特征", F_TEXT, gray)

# Feature bars
box(d, (610, 150, 640, 220), "#dbeafe", blue, 3, 3)
label(d, (625, 136), "图像特征", F_SMALL, blue)

box(d, (610, 570, 640, 640), "#dcfce7", green, 3, 3)
label(d, (625, 556), "点云特征", F_SMALL, green)

# Reliability and fusion modules
box(d, (730, 315, 960, 465), "#fff7ed", orange, 4, 10)
label(d, (845, 353), "可靠性权重生成", F_BOX)
label(d, (845, 388), "MLP + Softmax", F_TEXT, gray)
label(d, (845, 423), "图像权重 / 点云权重", F_TEXT, gray)

box(d, (1115, 315, 1315, 465), "#faf5ff", purple, 4, 10)
label(d, (1215, 352), "自适应融合", F_BOX)
label(d, (1215, 388), "门控加权 / 注意力", F_TEXT, gray)
label(d, (1215, 423), "加权Concat融合", F_TEXT, gray)

box(d, (1400, 338, 1545, 442), "#ecfeff", teal, 3, 8)
label(d, (1472, 373), "三维检测输出", F_BOX)
label(d, (1472, 407), "类别 / 置信度", F_SMALL, gray)
label(d, (1472, 430), "三维框", F_SMALL, gray)

# Split lines from inputs
arrow(d, (205, 195), (287, 185), blue, 3)
poly_arrow(d, [(205, 195), (250, 195), (250, 330), (287, 330)], blue, 3)

arrow(d, (205, 555), (287, 605), green, 3)
poly_arrow(d, [(205, 555), (250, 555), (250, 460), (287, 460)], green, 3)

# Feature flow to feature bars
arrow(d, (520, 185), (597, 185), blue, 3)
arrow(d, (520, 605), (597, 605), green, 3)

# Quality flow to reliability module
poly_arrow(d, [(520, 330), (655, 330), (655, 360), (717, 360)], blue, 3)
poly_arrow(d, [(520, 460), (655, 460), (655, 420), (717, 420)], green, 3)

# Feature flow to fusion
poly_arrow(d, [(640, 185), (1020, 185), (1020, 350), (1102, 350)], blue, 3)
poly_arrow(d, [(640, 605), (1020, 605), (1020, 430), (1102, 430)], green, 3)

# Reliability control and output flow
arrow(d, (960, 390), (1102, 390), orange, 3)
arrow(d, (1315, 390), (1387, 390), purple, 3)

# Result note
box(d, (730, 505, 960, 565), "#ffffff", orange, 2, 8)
label(d, (845, 528), "根据输入质量调整融合比例", F_SMALL, "#c2410c")
label(d, (845, 550), "降低退化模态干扰", F_SMALL, "#c2410c")
arrow(d, (845, 465), (845, 505), orange, 2)

box(d, (1115, 505, 1315, 565), "#ffffff", purple, 2, 8)
label(d, (1215, 528), "融合图像语义", F_SMALL, purple)
label(d, (1215, 550), "与点云几何信息", F_SMALL, purple)
arrow(d, (1215, 465), (1215, 505), purple, 2)

OUT.parent.mkdir(parents=True, exist_ok=True)
img.save(OUT)
print(OUT)

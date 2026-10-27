from __future__ import annotations

import datetime as dt
import os
import re
import shutil
import struct
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape


ROOT = Path(__file__).resolve().parents[1]
BASE_PPTX = Path(
    r"C:\Users\27452\.codex\plugins\cache\openai-curated-remote\openai-templates\0.1.1"
    r"\skills\artifact-template-simple-light-mode\assets\reference.pptx"
)
OUT_DIR = ROOT / "ppt"
OUT_PPTX = OUT_DIR / "复杂工况下三维目标检测方法研究_开题汇报.pptx"
BUILD_DIR = ROOT / ".codex_build" / "opening_report_ppt"
MEDIA_DIR = BUILD_DIR / "media"

SLIDE_W = 12192000
SLIDE_H = 6858000
EMU = 914400

FONT = "Microsoft YaHei"
BG = "FFFFFF"
NAVY = "12344D"
TEAL = "2A9D8F"
ORANGE = "E76F51"
GRAY_BG = "F4F7FA"
LINE = "D7DEE8"
TEXT = "1F2933"
MUTED = "5B677A"


def emu(inches: float) -> int:
    return int(round(inches * EMU))


def xml_text(text: str) -> str:
    return escape(text, {'"': "&quot;"})


def srgb(color: str) -> str:
    return color.replace("#", "").upper()


def png_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return struct.unpack(">II", data[16:24])
    if data[:2] == b"\xff\xd8":
        i = 2
        while i < len(data):
            if data[i] != 0xFF:
                i += 1
                continue
            marker = data[i + 1]
            i += 2
            if marker in (0xD8, 0xD9):
                continue
            length = struct.unpack(">H", data[i : i + 2])[0]
            if marker in range(0xC0, 0xC4):
                h, w = struct.unpack(">HH", data[i + 3 : i + 7])
                return w, h
            i += length
    raise ValueError(f"Unsupported image format: {path}")


def fit_image(path: Path, x: float, y: float, w: float, h: float) -> tuple[int, int, int, int]:
    iw, ih = png_size(path)
    box_w, box_h = emu(w), emu(h)
    scale = min(box_w / iw, box_h / ih)
    real_w = int(iw * scale)
    real_h = int(ih * scale)
    left = emu(x) + (box_w - real_w) // 2
    top = emu(y) + (box_h - real_h) // 2
    return left, top, real_w, real_h


class Slide:
    def __init__(self, index: int, total: int, title: str | None = None):
        self.index = index
        self.total = total
        self.parts: list[str] = []
        self.rels: list[str] = []
        self.next_id = 2
        self.next_rid = 2
        self.images: list[tuple[Path, str]] = []
        self.bg_color = BG
        if title:
            self.add_title(title)
            self.footer()

    def new_id(self) -> int:
        value = self.next_id
        self.next_id += 1
        return value

    def new_rid(self) -> str:
        value = f"rId{self.next_rid}"
        self.next_rid += 1
        return value

    def add_title(self, text: str):
        self.textbox(0.72, 0.38, 11.6, 0.55, text, 28, NAVY, bold=True)
        self.rect(0.72, 1.05, 1.15, 0.045, TEAL, TEAL, 0)

    def footer(self):
        self.textbox(11.75, 7.05, 0.9, 0.18, f"{self.index:02d}", 8, MUTED, align="r")

    def rect(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        fill: str = "FFFFFF",
        line: str = LINE,
        line_w: int = 6350,
        radius: str = "rect",
    ):
        sid = self.new_id()
        ln = (
            f'<a:ln w="{line_w}"><a:solidFill><a:srgbClr val="{srgb(line)}"/></a:solidFill></a:ln>'
            if line_w > 0
            else '<a:ln><a:noFill/></a:ln>'
        )
        self.parts.append(
            f'<p:sp><p:nvSpPr><p:cNvPr id="{sid}" name="Shape {sid}"/>'
            f"<p:cNvSpPr/><p:nvPr/></p:nvSpPr><p:spPr>"
            f'<a:xfrm><a:off x="{emu(x)}" y="{emu(y)}"/><a:ext cx="{emu(w)}" cy="{emu(h)}"/></a:xfrm>'
            f'<a:prstGeom prst="{radius}"><a:avLst/></a:prstGeom>'
            f'<a:solidFill><a:srgbClr val="{srgb(fill)}"/></a:solidFill>{ln}'
            f"</p:spPr></p:sp>"
        )

    def textbox(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        text: str | list[str],
        size: int = 18,
        color: str = TEXT,
        bold: bool = False,
        align: str = "l",
        fill: str | None = None,
        line: str | None = None,
        margin: int = 70000,
        valign: str = "top",
    ):
        sid = self.new_id()
        fill_xml = (
            f'<a:solidFill><a:srgbClr val="{srgb(fill)}"/></a:solidFill>'
            if fill
            else "<a:noFill/>"
        )
        line_xml = (
            f'<a:ln w="6350"><a:solidFill><a:srgbClr val="{srgb(line)}"/></a:solidFill></a:ln>'
            if line
            else '<a:ln><a:noFill/></a:ln>'
        )
        paragraphs = text if isinstance(text, list) else str(text).split("\n")
        p_xml = []
        bold_attr = 'b="1"' if bold else ""
        for para in paragraphs:
            p_xml.append(
                f'<a:p><a:pPr algn="{align}"/>'
                f'<a:r><a:rPr lang="zh-CN" sz="{size * 100}" '
                f'{bold_attr}>'
                f'<a:solidFill><a:srgbClr val="{srgb(color)}"/></a:solidFill>'
                f'<a:latin typeface="{FONT}"/><a:ea typeface="{FONT}"/><a:cs typeface="{FONT}"/>'
                f'</a:rPr><a:t>{xml_text(para)}</a:t></a:r></a:p>'
            )
        self.parts.append(
            f'<p:sp><p:nvSpPr><p:cNvPr id="{sid}" name="Text {sid}"/>'
            f"<p:cNvSpPr txBox=\"1\"/><p:nvPr/></p:nvSpPr>"
            f"<p:spPr>"
            f'<a:xfrm><a:off x="{emu(x)}" y="{emu(y)}"/><a:ext cx="{emu(w)}" cy="{emu(h)}"/></a:xfrm>'
            f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>{fill_xml}{line_xml}</p:spPr>'
            f'<p:txBody><a:bodyPr wrap="square" anchor="{valign}" lIns="{margin}" rIns="{margin}" '
            f'tIns="{margin}" bIns="{margin}"/><a:lstStyle/>'
            f'{"".join(p_xml)}</p:txBody></p:sp>'
        )

    def bullet_list(self, x: float, y: float, w: float, items: list[str], size: int = 18, gap: float = 0.48):
        for i, item in enumerate(items):
            top = y + i * gap
            self.rect(x, top + 0.13, 0.08, 0.08, TEAL, TEAL, 0)
            self.textbox(x + 0.18, top, w - 0.18, 0.36, item, size, TEXT, margin=0)

    def tag(self, x: float, y: float, label: str, fill: str = GRAY_BG, color: str = NAVY, w: float = 1.35):
        self.rect(x, y, w, 0.36, fill, fill, 0, "roundRect")
        self.textbox(x, y + 0.015, w, 0.28, label, 12, color, bold=True, align="c", margin=0, valign="mid")

    def card(self, x: float, y: float, w: float, h: float, title: str, body: str, accent: str = TEAL):
        self.rect(x, y, w, h, "FFFFFF", LINE, 9500, "roundRect")
        self.rect(x, y, 0.08, h, accent, accent, 0)
        self.textbox(x + 0.22, y + 0.18, w - 0.35, 0.28, title, 15, NAVY, bold=True, margin=0)
        self.textbox(x + 0.22, y + 0.55, w - 0.38, h - 0.68, body, 12, TEXT, margin=0)

    def flow_box(self, x: float, y: float, w: float, h: float, title: str, body: str, fill: str = GRAY_BG):
        self.rect(x, y, w, h, fill, LINE, 8000, "roundRect")
        self.textbox(x + 0.12, y + 0.12, w - 0.24, 0.28, title, 14, NAVY, bold=True, align="c", margin=0)
        self.textbox(x + 0.16, y + 0.48, w - 0.32, h - 0.55, body, 11, MUTED, align="c", margin=0)

    def line_arrow(self, x1: float, y1: float, x2: float, y2: float, color: str = LINE):
        sid = self.new_id()
        x = min(x1, x2)
        y = min(y1, y2)
        cx = abs(x2 - x1)
        cy = abs(y2 - y1)
        flip_h = ' flipH="1"' if x2 < x1 else ""
        flip_v = ' flipV="1"' if y2 < y1 else ""
        self.parts.append(
            f'<p:cxnSp><p:nvCxnSpPr><p:cNvPr id="{sid}" name="Connector {sid}"/>'
            f"<p:cNvCxnSpPr/><p:nvPr/></p:nvCxnSpPr><p:spPr>"
            f'<a:xfrm{flip_h}{flip_v}><a:off x="{emu(x)}" y="{emu(y)}"/><a:ext cx="{emu(cx)}" cy="{emu(cy)}"/></a:xfrm>'
            f'<a:prstGeom prst="straightConnector1"><a:avLst/></a:prstGeom>'
            f'<a:ln w="19050"><a:solidFill><a:srgbClr val="{srgb(color)}"/></a:solidFill>'
            f'<a:headEnd type="triangle"/></a:ln></p:spPr></p:cxnSp>'
        )

    def add_image(self, path: Path, x: float, y: float, w: float, h: float, name: str | None = None):
        path = path.resolve()
        rid = self.new_rid()
        sid = self.new_id()
        left, top, width, height = fit_image(path, x, y, w, h)
        media_name = name or f"image_s{self.index}_{len(self.images) + 1}{path.suffix.lower()}"
        self.images.append((path, media_name))
        self.rels.append(
            f'<Relationship Id="{rid}" '
            f'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" '
            f'Target="../media/{media_name}"/>'
        )
        self.parts.append(
            f'<p:pic><p:nvPicPr><p:cNvPr id="{sid}" name="{xml_text(media_name)}"/>'
            f'<p:cNvPicPr><a:picLocks noChangeAspect="1"/></p:cNvPicPr><p:nvPr/></p:nvPicPr>'
            f'<p:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></p:blipFill>'
            f'<p:spPr><a:xfrm><a:off x="{left}" y="{top}"/><a:ext cx="{width}" cy="{height}"/></a:xfrm>'
            f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></p:spPr></p:pic>'
        )

    def table(self, x: float, y: float, widths: list[float], row_h: float, rows: list[list[str]], header_fill: str = NAVY):
        total_w = sum(widths)
        self.rect(x, y, total_w, row_h * len(rows), "FFFFFF", LINE, 6350)
        cur_y = y
        for r, row in enumerate(rows):
            cur_x = x
            for c, text in enumerate(row):
                fill = header_fill if r == 0 else ("F8FAFC" if r % 2 == 0 else "FFFFFF")
                color = "FFFFFF" if r == 0 else TEXT
                self.rect(cur_x, cur_y, widths[c], row_h, fill, LINE, 6350)
                self.textbox(cur_x + 0.04, cur_y + 0.03, widths[c] - 0.08, row_h - 0.06, text, 10 if r else 11, color, bold=(r == 0), align="c", margin=0, valign="mid")
                cur_x += widths[c]
            cur_y += row_h

    def bar_pair(self, x: float, y: float, label: str, clean: float, complex_: float, max_v: float, unit: str = ""):
        self.textbox(x, y, 1.25, 0.22, label, 9, TEXT, margin=0)
        base_x = x + 1.3
        clean_w = 1.1 * clean / max_v
        comp_w = 1.1 * complex_ / max_v
        self.rect(base_x, y + 0.02, clean_w, 0.09, TEAL, TEAL, 0)
        self.rect(base_x, y + 0.16, comp_w, 0.09, ORANGE, ORANGE, 0)
        self.textbox(base_x + 1.18, y - 0.02, 0.65, 0.16, f"{clean:g}{unit}", 8, MUTED, margin=0)
        self.textbox(base_x + 1.18, y + 0.13, 0.65, 0.16, f"{complex_:g}{unit}", 8, MUTED, margin=0)

    def xml(self) -> str:
        content = "".join(self.parts)
        return (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
            'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
            'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">'
            '<p:cSld><p:bg><p:bgPr><a:solidFill><a:srgbClr val="FFFFFF"/></a:solidFill>'
            '</p:bgPr></p:bg><p:spTree>'
            '<p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>'
            '<p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/>'
            '<a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>'
            f"{content}</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sld>"
        )

    def rels_xml(self) -> str:
        rels = [
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>'
        ] + self.rels
        return (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            + "".join(rels)
            + "</Relationships>"
        )


def cover_slide(total: int) -> Slide:
    s = Slide(1, total)
    s.rect(0, 0, 13.333, 7.5, BG, BG, 0)
    s.rect(0, 0, 0.23, 7.5, NAVY, NAVY, 0)
    s.textbox(0.85, 0.75, 10.8, 0.42, "硕士学位论文开题汇报", 18, TEAL, bold=True, margin=0)
    s.textbox(0.82, 1.55, 10.8, 1.15, "复杂工况下三维目标检测方法研究", 36, NAVY, bold=True, margin=0)
    s.textbox(0.86, 3.0, 8.8, 0.44, "围绕智能驾驶复杂环境中的检测可靠性问题，开展基础系统复现、退化现象分析与鲁棒方法研究", 17, TEXT, margin=0)
    s.rect(0.86, 4.25, 4.6, 0.02, TEAL, TEAL, 0)
    s.textbox(0.86, 4.55, 4.7, 0.9, ["汇报人：", "导师：", "时间：2026年9月"], 14, MUTED, margin=0)
    s.rect(8.2, 4.55, 3.9, 1.05, GRAY_BG, GRAY_BG, 0, "roundRect")
    s.textbox(8.45, 4.78, 3.4, 0.52, "开题阶段重点", 14, NAVY, bold=True, align="c", margin=0)
    s.textbox(8.45, 5.2, 3.4, 0.22, "先复现基础系统，再分析复杂工况退化", 10, MUTED, align="c", margin=0)
    return s


def detection_status_slide(
    index: int,
    total: int,
    title: str,
    intro: str,
    flow: list[tuple[str, str]],
    bullets: list[str],
    image_path: Path,
    image_name: str,
    caption: str,
) -> Slide:
    s = Slide(index, total, title)
    s.textbox(0.85, 1.28, 11.65, 0.35, intro, 17, TEXT, margin=0)

    start_x = 0.85
    for i, (box_title, box_body) in enumerate(flow):
        x = start_x + i * 2.05
        s.flow_box(x, 1.95, 1.62, 0.96, box_title, box_body, "F5F8FA")
        if i < len(flow) - 1:
            s.line_arrow(x + 1.66, 2.43, x + 1.98, 2.43, TEAL)

    s.textbox(0.85, 3.42, 4.35, 0.34, "技术作用", 18, NAVY, bold=True, margin=0)
    s.bullet_list(0.85, 3.92, 4.55, bullets, 15, 0.47)

    s.rect(5.75, 1.65, 6.75, 4.65, "FFFFFF", LINE, 9500, "roundRect")
    s.add_image(image_path, 5.95, 1.82, 6.35, 4.05, image_name)
    s.textbox(5.95, 5.95, 6.35, 0.22, caption, 10, MUTED, align="c", margin=0)
    return s


def complex_compare_slide(
    index: int,
    total: int,
    title: str,
    image_path: Path,
    difference: str,
    result: str,
    reason: str,
    image_name: str,
) -> Slide:
    s = Slide(index, total, title)
    s.textbox(0.85, 1.22, 11.7, 0.28, "左侧为 clean 正常样例，右侧为 complex 复杂工况样例；两者输入同一类检测流程进行对比。", 13, MUTED, align="c", margin=0)
    s.rect(0.65, 1.62, 12.05, 2.28, "FFFFFF", LINE, 9500, "roundRect")
    s.add_image(image_path, 0.82, 1.77, 11.7, 1.96, image_name)

    s.card(0.95, 4.35, 3.55, 1.35, "两张图的区别", difference, TEAL)
    s.card(4.9, 4.35, 3.55, 1.35, "检测结果变化", result, ORANGE)
    s.card(8.85, 4.35, 3.55, 1.35, "可能原因", reason, TEAL)
    s.textbox(1.1, 6.28, 11.0, 0.3, "阶段性结论：复杂工况不一定让检测完全失败，但会降低检测结果的稳定性和可靠性。", 15, NAVY, bold=True, align="c", margin=0)
    return s


def build_slides() -> list[Slide]:
    total = 20
    slides: list[Slide] = [cover_slide(total)]

    s = Slide(2, total, "研究背景：三维感知支撑自动驾驶决策")
    s.card(0.8, 1.55, 3.45, 1.1, "环境感知", "识别道路目标和场景状态，是预测、规划与控制的前提")
    s.card(4.75, 1.55, 3.45, 1.1, "三维目标检测", "输出类别、位置、尺寸和朝向，更接近下游空间决策需求")
    s.card(8.7, 1.55, 3.45, 1.1, "复杂开放环境", "夜间、雾天、模糊、点云稀疏等因素会影响输入质量")
    s.line_arrow(4.25, 2.1, 4.65, 2.1, TEAL)
    s.line_arrow(8.2, 2.1, 8.6, 2.1, TEAL)
    s.textbox(0.9, 3.28, 11.3, 0.45, "研究重点从“能检测”转向“复杂工况下稳定检测”", 24, NAVY, bold=True, align="c", margin=0)
    s.bullet_list(2.1, 4.15, 8.8, [
        "标准数据集平均精度不能完全反映真实道路风险",
        "复杂工况可能造成漏检、置信度下降或三维框偏移",
        "需要结合图像、点云和融合链路分析模型退化原因",
    ], 18, 0.55)
    slides.append(s)

    s = Slide(3, total, "研究现状概述")
    s.textbox(0.9, 1.28, 11.5, 0.35, "智能驾驶三维感知相关研究可以从检测输入、空间输出和复杂工况鲁棒性三个层次理解。", 18, TEXT, align="c", margin=0)
    s.card(0.85, 2.0, 2.85, 1.28, "图像目标检测", "以相机图像为输入，识别目标类别和图像平面位置，是视觉感知基础。", TEAL)
    s.card(3.95, 2.0, 2.85, 1.28, "点云三维检测", "以激光雷达点云为输入，预测目标三维位置、尺寸和朝向。", ORANGE)
    s.card(7.05, 2.0, 2.85, 1.28, "多模态三维检测", "融合图像语义和点云几何信息，提升场景表达能力。", TEAL)
    s.card(10.15, 2.0, 2.45, 1.28, "复杂工况鲁棒性", "关注弱光、雾天、模糊和点云退化下的稳定性。", ORANGE)
    s.line_arrow(3.76, 2.64, 3.9, 2.64, LINE)
    s.line_arrow(6.86, 2.64, 7.0, 2.64, LINE)
    s.line_arrow(9.96, 2.64, 10.1, 2.64, LINE)
    s.rect(1.2, 4.35, 10.9, 1.1, GRAY_BG, GRAY_BG, 0, "roundRect")
    s.textbox(1.55, 4.62, 10.2, 0.28, "本课题关注点", 18, NAVY, bold=True, align="c", margin=0)
    s.textbox(1.7, 5.02, 9.9, 0.28, "在基础检测链路支撑下，分析复杂工况造成的检测退化，并在已有鲁棒方法基础上探索改进", 17, TEXT, align="c", margin=0)
    slides.append(s)

    slides.append(detection_status_slide(
        4,
        total,
        "研究现状：二维目标检测",
        "二维目标检测是相机视觉感知的基础任务，主要输出图像平面中的目标类别、置信度和二维框。",
        [
            ("道路图像", "相机输入"),
            ("特征提取", "纹理\n语义"),
            ("检测头", "类别\n置信度"),
            ("二维框", "图像位置"),
        ],
        [
            "适合识别车辆、行人、交通标志等视觉目标",
            "输出直观，便于展示基础检测流程",
            "不能直接提供真实三维距离、尺寸和朝向",
        ],
        ROOT / "code/outputs/stage01_2d_detection/bus_detected.jpg",
        "stage01_2d_detection.jpg",
        "二维检测流程验证结果：图像输入后输出目标类别和二维检测框",
    ))

    slides.append(detection_status_slide(
        5,
        total,
        "研究现状：单模态三维目标检测",
        "激光雷达点云能够提供空间几何信息，单模态三维检测主要根据点云估计目标三维框。",
        [
            ("点云输入", "LiDAR\n三维点"),
            ("点云编码", "pillar\nvoxel"),
            ("BEV 特征", "鸟瞰图\n表达"),
            ("三维框", "位置\n尺寸\n朝向"),
        ],
        [
            "空间定位能力较强，对光照变化不敏感",
            "点云远距离稀疏，局部缺失会削弱几何表达",
            "BEV 可视化便于观察目标在道路平面的位置",
        ],
        ROOT / "code/outputs/server_pointpillars_demo/000008_pred_bev.png",
        "pointpillars_bev.png",
        "PointPillars 复现结果：散点为点云，彩色框为三维框在 BEV 平面的投影",
    ))

    slides.append(detection_status_slide(
        6,
        total,
        "研究现状：图像-激光雷达多模态检测",
        "多模态三维检测利用图像语义和点云几何互补信息，是智能驾驶三维感知的重要方向。",
        [
            ("图像 + 点云", "同步输入\n标定信息"),
            ("特征提取", "语义\n几何"),
            ("融合检测", "特征级\n或候选级"),
            ("三维结果", "三维框\n投影展示"),
        ],
        [
            "图像提供纹理和语义，点云提供距离和空间结构",
            "融合效果依赖输入质量和跨模态对应关系",
            "复杂工况下需要进一步关注模态可靠性变化",
        ],
        ROOT / "code/outputs/stage03_mvxnet_demo/vis_camera/CAM2/000008.png",
        "mvxnet_camera.png",
        "MVX-Net 复现结果：模型输出三维框，并投影到相机图像中展示",
    ))

    s = Slide(7, total, "复杂工况改变传感器输入质量")
    conditions = [
        ("弱光", "亮度不足\n纹理减弱"),
        ("雾天", "对比度下降\n远处目标不清"),
        ("运动模糊", "边界模糊\n轮廓不稳定"),
        ("图像噪声", "颗粒干扰\n小目标受影响"),
        ("点云稀疏", "点数减少\n几何结构不足"),
        ("点云扰动", "点位置抖动\n定位可靠性下降"),
    ]
    for i, (title, body) in enumerate(conditions):
        x = 0.85 + (i % 3) * 4.12
        y = 1.55 + (i // 3) * 1.72
        accent = TEAL if i < 4 else ORANGE
        s.card(x, y, 3.45, 1.15, title, body, accent)
    s.textbox(1.0, 5.35, 11.25, 0.55, "复杂工况并不是单一问题，需要区分图像退化、点云退化和跨模态对应关系变化", 20, NAVY, bold=True, align="c", margin=0)
    slides.append(s)

    s = Slide(8, total, "科学问题")
    s.rect(1.15, 1.48, 11.0, 1.25, GRAY_BG, GRAY_BG, 0, "roundRect")
    s.textbox(1.55, 1.75, 10.2, 0.55, "复杂工况下，图像和点云输入质量退化如何影响三维目标检测结果，如何提升模型鲁棒性？", 24, NAVY, bold=True, align="c", margin=0)
    s.card(1.05, 3.45, 3.25, 1.15, "退化表征", "将夜间、雾天、模糊、噪声和点云退化转化为可实验样例")
    s.card(5.0, 3.45, 3.25, 1.15, "影响分析", "结合检测数量、置信度、高置信目标和可视化结果分析退化现象")
    s.card(8.95, 3.45, 3.25, 1.15, "鲁棒提升", "在已有方法基础上探索数据增强、可靠性评估和融合策略改进")
    s.line_arrow(4.42, 4.05, 4.9, 4.05, TEAL)
    s.line_arrow(8.37, 4.05, 8.85, 4.05, TEAL)
    slides.append(s)

    s = Slide(9, total, "现有方法不足")
    s.card(0.95, 1.45, 3.45, 1.4, "单模态适应能力有限", "图像方法受光照和成像质量影响；点云方法受稀疏性和测量误差影响", TEAL)
    s.card(4.95, 1.45, 3.45, 1.4, "融合方法质量感知不足", "多模态融合依赖输入质量和空间对应关系，退化模态可能影响整体结果", ORANGE)
    s.card(8.95, 1.45, 3.45, 1.4, "复杂工况评测不足", "仅看整体平均精度难以解释不同退化类型下的可靠性变化", TEAL)
    s.textbox(1.05, 3.75, 11.2, 0.5, "本课题路线", 22, NAVY, bold=True, align="c", margin=0)
    s.flow_box(1.1, 4.55, 2.2, 0.75, "基础链路", "先跑通检测系统")
    s.flow_box(3.9, 4.55, 2.2, 0.75, "工况构造", "形成成对样例")
    s.flow_box(6.7, 4.55, 2.2, 0.75, "退化分析", "观察输出变化")
    s.flow_box(9.5, 4.55, 2.2, 0.75, "方法改进", "基于已有方法优化")
    s.line_arrow(3.35, 4.93, 3.82, 4.93, TEAL)
    s.line_arrow(6.15, 4.93, 6.62, 4.93, TEAL)
    s.line_arrow(8.95, 4.93, 9.42, 4.93, TEAL)
    slides.append(s)

    s = Slide(10, total, "总体技术路线")
    steps = [
        ("公开数据", "KITTI 等\n图像 点云 标定"),
        ("基础检测系统", "二维检测\nPointPillars\nMVX-Net"),
        ("复杂工况构造", "图像退化\n点云退化"),
        ("成对检测对比", "clean 样例\ncomplex 样例"),
        ("退化规律分析", "置信度\n漏检\n高置信目标"),
        ("鲁棒方法探索", "已有方法基础上\n进行改进"),
    ]
    for i, (title, body) in enumerate(steps):
        x = 0.65 + i * 2.08
        fill = "F3FAF8" if i % 2 == 0 else "F8FAFC"
        s.flow_box(x, 2.0, 1.7, 1.25, title, body, fill)
        if i < len(steps) - 1:
            s.line_arrow(x + 1.73, 2.62, x + 2.0, 2.62, TEAL)
    s.textbox(1.1, 4.25, 10.95, 0.42, "核心原则：先用实验链路把问题做出来，再选择已有鲁棒方法作为改进基础", 21, NAVY, bold=True, align="c", margin=0)
    s.bullet_list(2.25, 5.1, 8.8, [
        "不把尚未实现的复杂算法写成既定结果",
        "不夸大少量样例的结论",
        "后续通过扩充数据和指标评价增强说服力",
    ], 16, 0.44)
    slides.append(s)

    s = Slide(11, total, "前期已完成工作")
    s.textbox(0.9, 1.32, 11.6, 0.35, "二维、单模态三维、多模态三维检测已完成基础复现，前期重点进一步转向复杂工况退化现象复现。", 18, TEXT, align="c", margin=0)
    s.card(0.9, 2.0, 3.55, 1.12, "基础复现", "YOLOv8、PointPillars、MVX-Net 三类基础检测流程已跑通", TEAL)
    s.card(4.9, 2.0, 3.55, 1.12, "复杂工况构造", "构造 clean / complex 成对样例，覆盖图像退化和点云退化", ORANGE)
    s.card(8.9, 2.0, 3.55, 1.12, "退化对比分析", "比较检测数量、平均置信度和高置信目标数量变化", TEAL)
    s.rect(1.2, 4.0, 10.9, 1.25, GRAY_BG, GRAY_BG, 0, "roundRect")
    s.textbox(1.6, 4.25, 10.1, 0.34, "汇报重点", 19, NAVY, bold=True, align="c", margin=0)
    s.textbox(1.8, 4.78, 9.7, 0.3, "通过复杂工况前后检测结果对比，说明现有多模态三维检测在复杂环境下仍存在稳定性下降风险", 18, TEXT, align="c", margin=0)
    slides.append(s)

    s = Slide(12, total, "复杂工况样例构造")
    s.textbox(0.9, 1.45, 11.6, 0.42, "采用 clean / complex 成对结构，便于观察同类场景在退化前后的检测变化", 21, NAVY, bold=True, align="c", margin=0)
    s.flow_box(1.0, 2.35, 2.4, 1.0, "原始样例", "图像\n点云\n标定信息")
    s.flow_box(4.15, 2.35, 2.4, 1.0, "退化构造", "弱光 雾天 模糊\n噪声 稀疏 扰动")
    s.flow_box(7.3, 2.35, 2.4, 1.0, "成对输入", "clean\ncomplex")
    s.flow_box(10.45, 2.35, 1.95, 1.0, "结果比较", "数量\n置信度\n漏检")
    s.line_arrow(3.5, 2.85, 4.05, 2.85, TEAL)
    s.line_arrow(6.65, 2.85, 7.2, 2.85, TEAL)
    s.line_arrow(9.8, 2.85, 10.35, 2.85, TEAL)
    rows = [
        ["工况类型", "对应退化来源"],
        ["弱光 / 雾天 / 模糊 / 噪声", "图像质量下降"],
        ["点云稀疏 / 点云扰动", "几何信息退化"],
        ["成对检测对比", "分析检测可靠性变化"],
    ]
    s.table(2.0, 4.35, [3.0, 5.6], 0.45, rows)
    slides.append(s)

    compare_specs = [
        (
            13,
            "复杂工况对比：弱光",
            ROOT / "code/outputs/stage04_complex_conditions/detection_comparisons/000008_low_light_clean_vs_complex_detection.png",
            "complex 图像整体亮度降低，目标纹理和背景细节变弱。",
            "检测数量 11→11，平均置信度 0.64→0.59，高置信目标数量基本不变。",
            "该样例中点云几何信息仍然可用，弱光主要削弱图像语义，因此影响相对较轻。",
            "low_light_compare.png",
        ),
        (
            14,
            "复杂工况对比：雾天",
            ROOT / "code/outputs/stage04_complex_conditions/detection_comparisons/000021_fog_clean_vs_complex_detection.png",
            "complex 图像对比度降低，远处目标边缘更不清晰。",
            "检测数量 12→12，平均置信度 0.53→0.48，高置信目标 5→4。",
            "雾化会削弱图像可见性，但点云仍提供空间约束，因此主要表现为置信度下降。",
            "fog_compare.png",
        ),
        (
            15,
            "复杂工况对比：运动模糊",
            ROOT / "code/outputs/stage04_complex_conditions/detection_comparisons/000022_motion_blur_clean_vs_complex_detection.png",
            "complex 图像目标边界被拉宽，车辆轮廓和纹理不如 clean 清晰。",
            "检测数量 4→4，但平均置信度 0.38→0.25，检测稳定性明显下降。",
            "运动模糊会破坏视觉特征，融合模型可用的图像语义变弱，导致置信度降低。",
            "motion_blur_compare.png",
        ),
        (
            16,
            "复杂工况对比：图像噪声",
            ROOT / "code/outputs/stage04_complex_conditions/detection_comparisons/000023_image_noise_clean_vs_complex_detection.png",
            "complex 图像出现颗粒和杂色，局部纹理被噪声干扰。",
            "检测数量 3→2，出现目标漏检，高置信目标数量下降到 0。",
            "噪声会干扰目标外观和边缘信息，小目标或弱目标更容易被漏掉。",
            "image_noise_compare.png",
        ),
        (
            17,
            "复杂工况对比：点云稀疏",
            ROOT / "code/outputs/stage04_complex_conditions/detection_comparisons/000024_lidar_sparse_clean_vs_complex_detection.png",
            "complex 点云点数明显减少，目标表面几何结构不完整。",
            "检测数量 4→3，高置信目标 2→1，出现漏检。",
            "点云稀疏会削弱三维几何证据，即使图像存在，三维框定位仍会受到影响。",
            "lidar_sparse_compare.png",
        ),
        (
            18,
            "复杂工况对比：点云扰动",
            ROOT / "code/outputs/stage04_complex_conditions/detection_comparisons/000025_lidar_jitter_clean_vs_complex_detection.png",
            "complex 点云位置发生抖动，几何对应关系不如 clean 稳定。",
            "检测数量 11→11，但平均置信度 0.61→0.33，高置信目标 4→0。",
            "点云扰动会破坏空间结构和标定对应，模型仍能给出框，但可靠性显著下降。",
            "lidar_jitter_compare.png",
        ),
    ]
    for spec in compare_specs:
        slides.append(complex_compare_slide(spec[0], total, *spec[1:]))

    s = Slide(19, total, "复杂工况结果统计与后续研究")
    stats = [
        ("弱光", 0.64, 0.59, 5, 5),
        ("雾天", 0.53, 0.48, 5, 4),
        ("运动模糊", 0.38, 0.25, 0, 0),
        ("图像噪声", 0.30, 0.32, 0, 0),
        ("点云稀疏", 0.55, 0.56, 2, 1),
        ("点云扰动", 0.61, 0.33, 4, 0),
    ]
    s.textbox(0.9, 1.35, 5.4, 0.34, "平均置信度变化", 18, NAVY, bold=True, margin=0)
    for i, (label, clean, comp, _, _) in enumerate(stats):
        s.bar_pair(0.95, 1.9 + i * 0.45, label, clean, comp, 0.7)
    s.textbox(7.0, 1.35, 5.4, 0.34, "高置信目标数量变化", 18, NAVY, bold=True, margin=0)
    for i, (label, _, _, clean, comp) in enumerate(stats):
        s.bar_pair(7.05, 1.9 + i * 0.45, label, clean, comp, 5)
    s.rect(2.55, 5.15, 0.2, 0.1, TEAL, TEAL, 0)
    s.textbox(2.82, 5.05, 1.1, 0.24, "clean", 10, MUTED, margin=0)
    s.rect(4.0, 5.15, 0.2, 0.1, ORANGE, ORANGE, 0)
    s.textbox(4.27, 5.05, 1.3, 0.24, "complex", 10, MUTED, margin=0)
    s.textbox(1.1, 5.85, 11.0, 0.44, "初步现象：部分复杂工况会造成置信度下降、高置信目标减少或少量漏检", 20, NAVY, bold=True, align="c", margin=0)
    slides.append(s)

    s = Slide(20, total, "拟开展研究内容与工作计划")
    s.card(0.85, 1.35, 2.8, 1.1, "完善数据构造", "扩充样例，设置退化类型和强度", TEAL)
    s.card(3.9, 1.35, 2.8, 1.1, "建立评价指标", "补充漏检、置信度、AP/mAP 等指标", ORANGE)
    s.card(6.95, 1.35, 2.8, 1.1, "分析退化差异", "区分图像退化和点云退化影响", TEAL)
    s.card(10.0, 1.35, 2.8, 1.1, "探索改进方法", "基于已有鲁棒方法进行适度改进", ORANGE)
    rows = [
        ["阶段", "时间", "主要内容", "阶段成果"],
        ["1", "2026.09-2026.10", "整理开题报告和展示材料", "开题报告"],
        ["2", "2026.10-2026.12", "扩充复杂工况样例", "成对数据样例"],
        ["3", "2026.12-2027.02", "统计分析复杂工况检测结果", "退化规律"],
        ["4", "2027.02-2027.04", "在已有方法基础上设计改进", "初步实验"],
        ["5", "2027.04-2027.06", "整理实验并撰写论文", "论文定稿"],
    ]
    s.table(0.85, 3.1, [0.7, 1.75, 5.35, 3.55], 0.47, rows)
    s.textbox(1.2, 6.25, 10.8, 0.35, "预期形成：复杂工况样例与评测结果、基于已有方法的改进方案、论文实验图表", 17, NAVY, bold=True, align="c", margin=0)
    slides.append(s)

    return slides


def update_content_types(xml: str, slide_count: int) -> str:
    xml = re.sub(r'<Override PartName="/ppt/slides/slide\d+\.xml"[^>]*/>', "", xml)
    xml = re.sub(r'<Override PartName="/ppt/notesSlides/notesSlide\d+\.xml"[^>]*/>', "", xml)
    xml = re.sub(r'<Override PartName="/ppt/charts/[^"]+"[^>]*/>', "", xml)
    xml = re.sub(r'<Override PartName="/ppt/embeddings/[^"]+"[^>]*/>', "", xml)
    inserts = "".join(
        f'<Override PartName="/ppt/slides/slide{i}.xml" '
        f'ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>'
        for i in range(1, slide_count + 1)
    )
    xml = xml.replace("</Types>", inserts + "</Types>")
    if '<Default Extension="png"' not in xml:
        xml = xml.replace(
            "</Types>",
            '<Default Extension="png" ContentType="image/png"/></Types>',
        )
    if '<Default Extension="jpg"' not in xml:
        xml = xml.replace(
            "</Types>",
            '<Default Extension="jpg" ContentType="image/jpeg"/></Types>',
        )
    return xml


def update_presentation_xml(xml: str, slide_count: int) -> str:
    ids = "".join(f'<p:sldId id="{300 + i}" r:id="rId{200 + i}"/>' for i in range(1, slide_count + 1))
    xml = re.sub(r"<p:sldIdLst>.*?</p:sldIdLst>", f"<p:sldIdLst>{ids}</p:sldIdLst>", xml, flags=re.S)
    return xml


def update_presentation_rels(xml: str, slide_count: int) -> str:
    xml = re.sub(
        r'<Relationship Id="[^"]+" Type="http://schemas\.openxmlformats\.org/officeDocument/2006/relationships/slide" Target="slides/slide\d+\.xml"/>',
        "",
        xml,
    )
    inserts = "".join(
        f'<Relationship Id="rId{200 + i}" '
        f'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" '
        f'Target="slides/slide{i}.xml"/>'
        for i in range(1, slide_count + 1)
    )
    xml = xml.replace("</Relationships>", inserts + "</Relationships>")
    return xml


def update_app_xml(xml: str, slide_count: int) -> str:
    xml = re.sub(r"<Slides>\d+</Slides>", f"<Slides>{slide_count}</Slides>", xml)
    return xml


def package(slides: list[Slide]):
    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)
    MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(exist_ok=True)

    skip_prefixes = (
        "ppt/slides/",
        "ppt/slides/_rels/",
        "ppt/notesSlides/",
        "ppt/notesSlides/_rels/",
        "ppt/charts/",
        "ppt/charts/_rels/",
        "ppt/embeddings/",
        "ppt/media/",
    )

    written_media: set[str] = set()
    with zipfile.ZipFile(BASE_PPTX, "r") as zin, zipfile.ZipFile(OUT_PPTX, "w", compression=zipfile.ZIP_DEFLATED) as zout:
        names = set(zin.namelist())
        for name in zin.namelist():
            if name == "[Content_Types].xml":
                data = update_content_types(zin.read(name).decode("utf-8"), len(slides)).encode("utf-8")
            elif name == "ppt/presentation.xml":
                data = update_presentation_xml(zin.read(name).decode("utf-8"), len(slides)).encode("utf-8")
            elif name == "ppt/_rels/presentation.xml.rels":
                data = update_presentation_rels(zin.read(name).decode("utf-8"), len(slides)).encode("utf-8")
            elif name == "docProps/app.xml":
                data = update_app_xml(zin.read(name).decode("utf-8"), len(slides)).encode("utf-8")
            elif name.startswith(skip_prefixes):
                continue
            else:
                data = zin.read(name)
            zout.writestr(name, data)

        for slide in slides:
            zout.writestr(f"ppt/slides/slide{slide.index}.xml", slide.xml())
            zout.writestr(f"ppt/slides/_rels/slide{slide.index}.xml.rels", slide.rels_xml())
            for image_path, media_name in slide.images:
                if media_name in written_media:
                    continue
                written_media.add(media_name)
                zout.writestr(f"ppt/media/{media_name}", image_path.read_bytes())


def main():
    if not BASE_PPTX.exists():
        raise FileNotFoundError(BASE_PPTX)
    slides = build_slides()
    package(slides)
    print(OUT_PPTX)


if __name__ == "__main__":
    main()

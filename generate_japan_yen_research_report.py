#!/usr/bin/env python3
from __future__ import annotations

import math
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
OUT_DIR = ROOT / "output" / "pdf"
TMP_DIR = ROOT / "tmp" / "pdfs" / "japan_yen_research_report"
OUT_DIR.mkdir(parents=True, exist_ok=True)
TMP_DIR.mkdir(parents=True, exist_ok=True)


TITLE = "日元的镜像：日本资产泡沫、资产负债表衰退与全球流动性外溢"
SUBTITLE = "宏观研究报告"
REPORT_DATE = "2026-03-30"
PDF_PATH = OUT_DIR / "japan_yen_liquidity_research_report.pdf"


FONT_CANDIDATES = {
    "title": [
        "/System/Library/Fonts/STHeiti Medium.ttc",
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
        "/Library/Fonts/Arial Unicode.ttf",
    ],
    "body": [
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
        "/System/Library/Fonts/STHeiti Light.ttc",
        "/Library/Fonts/Arial Unicode.ttf",
    ],
    "body_bold": [
        "/System/Library/Fonts/STHeiti Medium.ttc",
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
        "/Library/Fonts/Arial Unicode.ttf",
    ],
}


def load_font(paths: list[str], size: int) -> ImageFont.FreeTypeFont:
    last_error: Exception | None = None
    for path in paths:
        try:
            return ImageFont.truetype(path, size)
        except Exception as exc:  # pragma: no cover - best effort font loading
            last_error = exc
    raise RuntimeError(f"Unable to load font from candidates: {paths}") from last_error


def make_fonts() -> dict[str, ImageFont.FreeTypeFont]:
    return {
        "title": load_font(FONT_CANDIDATES["title"], 50),
        "subtitle": load_font(FONT_CANDIDATES["body_bold"], 22),
        "section": load_font(FONT_CANDIDATES["body_bold"], 29),
        "subsection": load_font(FONT_CANDIDATES["body_bold"], 24),
        "body": load_font(FONT_CANDIDATES["body"], 22),
        "body_small": load_font(FONT_CANDIDATES["body"], 18),
        "body_tiny": load_font(FONT_CANDIDATES["body"], 15),
        "label": load_font(FONT_CANDIDATES["body_bold"], 18),
        "table_head": load_font(FONT_CANDIDATES["body_bold"], 18),
    }


FONTS = make_fonts()


def font_line_height(font: ImageFont.FreeTypeFont, scale: float = 1.55) -> int:
    return int(font.size * scale)


TOKEN_RE = re.compile(r"([A-Za-z0-9:/._%-]+|\s+|.)", re.S)


def tokenize(text: str) -> list[str]:
    return TOKEN_RE.findall(text)


def wrap_paragraph(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    tokens = tokenize(text.replace("\t", " "))
    lines: list[str] = []
    current = ""

    def flush() -> None:
        nonlocal current
        if current.strip():
            lines.append(current.rstrip())
        current = ""

    for token in tokens:
        if token == "\n":
            flush()
            continue

        if token.isspace():
            if not current:
                continue
            candidate = current + " "
            if draw.textlength(candidate, font=font) <= max_width:
                current = candidate
            else:
                flush()
            continue

        candidate = current + token
        if draw.textlength(candidate, font=font) <= max_width:
            current = candidate
            continue

        if current:
            flush()
        current = token.lstrip()
        if draw.textlength(current, font=font) <= max_width:
            continue

        # Very long tokens such as URLs are split character by character.
        current = ""
        for ch in token:
            candidate = current + ch
            if draw.textlength(candidate, font=font) <= max_width:
                current = candidate
            else:
                if current:
                    lines.append(current)
                current = ch

    flush()
    return lines


class ReportCanvas:
    def __init__(self, page_w: int, page_h: int, margin_x: int = 90, top_margin: int = 104, bottom_margin: int = 92):
        self.page_w = page_w
        self.page_h = page_h
        self.margin_x = margin_x
        self.top_margin = top_margin
        self.bottom_margin = bottom_margin
        self.content_x = margin_x
        self.content_w = page_w - 2 * margin_x
        self.pages: list[Image.Image] = []
        self.draws: list[ImageDraw.ImageDraw] = []
        self.current_y = top_margin
        self._new_body_page()

    def _new_body_page(self) -> None:
        img = Image.new("RGB", (self.page_w, self.page_h), "white")
        draw = ImageDraw.Draw(img)
        # Header bar
        draw.rectangle((0, 0, self.page_w, 18), fill="#1D3557")
        draw.rectangle((0, 18, self.page_w, 34), fill="#D9E5F0")
        draw.text((self.margin_x, 44), TITLE, font=FONTS["body_small"], fill="#34495E")
        draw.line((self.margin_x, 84, self.page_w - self.margin_x, 84), fill="#CBD5E1", width=2)
        self.pages.append(img)
        self.draws.append(draw)
        self.current_y = self.top_margin

    @property
    def draw(self) -> ImageDraw.ImageDraw:
        return self.draws[-1]

    def ensure_space(self, height: int) -> None:
        if self.current_y + height > self.page_h - self.bottom_margin:
            self._new_body_page()

    def add_space(self, height: int) -> None:
        self.current_y += height

    def add_title_page(self) -> None:
        img = Image.new("RGB", (self.page_w, self.page_h), "white")
        draw = ImageDraw.Draw(img)

        draw.rectangle((0, 0, self.page_w, 30), fill="#1D3557")
        draw.rectangle((0, 30, self.page_w, 64), fill="#EAF2F8")
        draw.rectangle((64, 126, self.page_w - 64, 132), fill="#1D3557")
        draw.text((90, 160), SUBTITLE, font=FONTS["subtitle"], fill="#657786")

        title_lines = wrap_paragraph(draw, TITLE, FONTS["title"], self.page_w - 180)
        draw.multiline_text((90, 210), "\n".join(title_lines), font=FONTS["title"], fill="#14213D", spacing=12)
        title_h = len(title_lines) * font_line_height(FONTS["title"], 1.12)
        draw.text((90, 210 + title_h + 18), "日本80-90年代泡沫破裂机理与现代日元融资外溢", font=FONTS["subtitle"], fill="#1D3557")

        summary_box = (90, 380, self.page_w - 90, 750)
        draw.rounded_rectangle(summary_box, radius=26, fill="#F7FAFC", outline="#C9D6E2", width=3)
        draw.text((120, 410), "核心判断", font=FONTS["section"], fill="#1D3557")
        key_points = [
            "宽松流动性通过银行信贷进入房地产和股市，依靠抵押品升值形成正反馈闭环。",
            "1989-1990年的加息和房地产贷款管制切断了信用扩张链条，泡沫迅速转入去杠杆。",
            "泡沫破裂后，日本长期低利率并未恢复内生信贷，而是把日元推成全球融资货币。",
        ]
        y = 470
        for point in key_points:
            lines = wrap_paragraph(draw, point, FONTS["body"], self.page_w - 210)
            draw.text((126, y), "•", font=FONTS["body"], fill="#1D3557")
            draw.multiline_text((154, y), "\n".join(lines), font=FONTS["body"], fill="#2B2F33", spacing=10)
            y += len(lines) * font_line_height(FONTS["body"]) + 18

        abstract_box = (90, 780, self.page_w - 90, 1120)
        draw.rounded_rectangle(abstract_box, radius=26, fill="#FFF9F2", outline="#E2C9A7", width=3)
        draw.text((120, 810), "摘要", font=FONTS["section"], fill="#8A5A44")
        abstract_text = (
            "本文把流动性界定为央行投放的基础货币与商业银行创造的广义信贷之和。"
            "日本80-90年代泡沫的本质，不是资产价格偶然失真，而是宽松信用通过银行体系流入房地产和股市，"
            "并借助抵押品升值形成自我强化的价格-信用循环。"
        )
        abstract_text2 = (
            "泡沫破裂后，日本进入资产负债表衰退。私人部门优先去杠杆而不是扩张投资，"
            "低利率与量化宽松并未重新激活内生信贷，却把日元塑造成全球融资货币，"
            "套息交易因此成为全球风险资产的重要边际杠杆。"
        )
        abstract_y = 872
        for paragraph in [abstract_text, abstract_text2]:
            lines = wrap_paragraph(draw, paragraph, FONTS["body"], self.page_w - 220)
            draw.multiline_text((120, abstract_y), "\n".join(lines), font=FONTS["body"], fill="#2B2F33", spacing=10)
            abstract_y += len(lines) * font_line_height(FONTS["body"]) + 18

        footer_text = f"Research Report | {REPORT_DATE}"
        bbox = draw.textbbox((0, 0), footer_text, font=FONTS["body_tiny"])
        fw = bbox[2] - bbox[0]
        draw.text((self.page_w - 90 - fw, self.page_h - 76), footer_text, font=FONTS["body_tiny"], fill="#6B7280")
        draw.text((90, self.page_h - 76), "Generated with local layout tooling", font=FONTS["body_tiny"], fill="#6B7280")

        self.pages.insert(0, img)
        self.draws.insert(0, draw)
        self.current_y = self.top_margin

    def add_section_title(self, title: str) -> None:
        draw = self.draw
        height = font_line_height(FONTS["section"], 1.3)
        self.ensure_space(height + 24)
        draw.text((self.content_x, self.current_y), title, font=FONTS["section"], fill="#1D3557")
        self.current_y += height
        draw.line((self.content_x, self.current_y + 8, self.content_x + 240, self.current_y + 8), fill="#1D3557", width=3)
        self.current_y += 22

    def add_subsection_title(self, title: str) -> None:
        draw = self.draw
        height = font_line_height(FONTS["subsection"], 1.2)
        self.ensure_space(height + 18)
        draw.text((self.content_x, self.current_y), title, font=FONTS["subsection"], fill="#334155")
        self.current_y += height + 12

    def add_paragraph(self, text: str, font: ImageFont.FreeTypeFont | None = None, fill: str = "#2B2F33", indent: int = 0, spacing: int = 10) -> None:
        draw = self.draw
        font = font or FONTS["body"]
        lines = wrap_paragraph(draw, text, font, self.content_w - indent)
        height = len(lines) * font_line_height(font) + spacing
        self.ensure_space(height + 12)
        x = self.content_x + indent
        y = self.current_y
        draw.multiline_text((x, y), "\n".join(lines), font=font, fill=fill, spacing=10)
        self.current_y += len(lines) * font_line_height(font) + spacing

    def add_bullet_list(self, items: list[str], bullet_color: str = "#1D3557", font: ImageFont.FreeTypeFont | None = None, spacing: int = 10) -> None:
        draw = self.draw
        font = font or FONTS["body"]
        bullet_w = draw.textlength("•", font=font)
        for item in items:
            lines = wrap_paragraph(draw, item, font, self.content_w - 46)
            height = len(lines) * font_line_height(font) + spacing + 2
            self.ensure_space(height + 8)
            draw.text((self.content_x, self.current_y), "•", font=font, fill=bullet_color)
            draw.multiline_text((self.content_x + 26, self.current_y), "\n".join(lines), font=font, fill="#2B2F33", spacing=10)
            self.current_y += len(lines) * font_line_height(font) + spacing

    def add_numbered_list(self, items: list[str], font: ImageFont.FreeTypeFont | None = None) -> None:
        draw = self.draw
        font = font or FONTS["body"]
        for idx, item in enumerate(items, start=1):
            prefix = f"{idx}."
            lines = wrap_paragraph(draw, item, font, self.content_w - 54)
            height = len(lines) * font_line_height(font) + 10
            self.ensure_space(height + 8)
            draw.text((self.content_x, self.current_y), prefix, font=font, fill="#1D3557")
            draw.multiline_text((self.content_x + 36, self.current_y), "\n".join(lines), font=font, fill="#2B2F33", spacing=10)
            self.current_y += len(lines) * font_line_height(font) + 10

    def add_box(self, title: str, paragraphs: list[str], fill: str, outline: str, title_color: str, body_fill: str | None = None) -> None:
        draw = self.draw
        body_fill = body_fill or "#2B2F33"
        top_pad = 20
        left_pad = 24
        right_pad = 24
        bottom_pad = 18
        max_text_width = self.content_w - left_pad - right_pad
        title_height = font_line_height(FONTS["section"], 1.15)
        para_lines: list[list[str]] = []
        total_line_count = 0
        for para in paragraphs:
            lines = wrap_paragraph(draw, para, FONTS["body"], max_text_width)
            para_lines.append(lines)
            total_line_count += len(lines)
        height = top_pad + title_height + 14 + total_line_count * font_line_height(FONTS["body"]) + len(paragraphs) * 10 + bottom_pad
        self.ensure_space(height + 18)
        box = (self.content_x, self.current_y, self.content_x + self.content_w, self.current_y + height)
        draw.rounded_rectangle(box, radius=18, fill=fill, outline=outline, width=3)
        draw.text((self.content_x + left_pad, self.current_y + 16), title, font=FONTS["section"], fill=title_color)
        y = self.current_y + 16 + title_height + 10
        for lines in para_lines:
            draw.multiline_text((self.content_x + left_pad, y), "\n".join(lines), font=FONTS["body"], fill=body_fill, spacing=10)
            y += len(lines) * font_line_height(FONTS["body"]) + 12
        self.current_y += height + 18

    def add_flow_diagram(self, title: str, labels: list[str], subtitle: str | None = None) -> None:
        draw = self.draw
        top_pad = 20
        inner_pad_x = 24
        inner_pad_y = 18
        gap = 18
        box_h = 74
        title_h = font_line_height(FONTS["section"], 1.15)
        subtitle_h = font_line_height(FONTS["body_small"], 1.1) if subtitle else 0
        area_h = top_pad + title_h + (10 if subtitle else 0) + subtitle_h + inner_pad_y + box_h + 56
        self.ensure_space(area_h + 12)

        x0 = self.content_x
        y0 = self.current_y
        draw.rounded_rectangle((x0, y0, x0 + self.content_w, y0 + area_h), radius=18, fill="#FFFDF8", outline="#E6CBA8", width=3)
        draw.text((x0 + inner_pad_x, y0 + 16), title, font=FONTS["section"], fill="#8A5A44")
        cursor_y = y0 + 16 + title_h + 8
        if subtitle:
            lines = wrap_paragraph(draw, subtitle, FONTS["body_small"], self.content_w - 2 * inner_pad_x)
            draw.multiline_text((x0 + inner_pad_x, cursor_y), "\n".join(lines), font=FONTS["body_small"], fill="#8A5A44", spacing=8)
            cursor_y += len(lines) * font_line_height(FONTS["body_small"]) + 10

        available_w = self.content_w - 2 * inner_pad_x
        box_w = min(170, (available_w - gap * (len(labels) - 1)) // len(labels))
        total_boxes_w = len(labels) * box_w + (len(labels) - 1) * gap
        start_x = x0 + (self.content_w - total_boxes_w) / 2
        box_y = cursor_y + 16

        def draw_arrow(x1: float, x2: float, y: float) -> None:
            draw.line((x1, y, x2, y), fill="#C97B63", width=4)
            head = 10
            draw.polygon([(x2, y), (x2 - head, y - 6), (x2 - head, y + 6)], fill="#C97B63")

        for idx, label in enumerate(labels):
            bx = start_x + idx * (box_w + gap)
            box = (bx, box_y, bx + box_w, box_y + box_h)
            fill = "#F7FAFC" if idx % 2 == 0 else "#EEF4FA"
            draw.rounded_rectangle(box, radius=14, fill=fill, outline="#BFD0E3", width=2)
            lines = wrap_paragraph(draw, label, FONTS["body_small"], box_w - 20)
            text_h = len(lines) * font_line_height(FONTS["body_small"], 1.1)
            text_y = box_y + (box_h - text_h) / 2 - 2
            draw.multiline_text((bx + 10, text_y), "\n".join(lines), font=FONTS["body_small"], fill="#1D3557", spacing=6, align="center")
            if idx < len(labels) - 1:
                draw_arrow(bx + box_w + 4, bx + box_w + gap - 4, box_y + box_h / 2)

        loop_text = "正反馈闭环"
        pill_w = 150
        pill_h = 36
        pill_x = x0 + (self.content_w - pill_w) / 2
        pill_y = box_y + box_h + 14
        draw.rounded_rectangle((pill_x, pill_y, pill_x + pill_w, pill_y + pill_h), radius=18, fill="#FFF4EC", outline="#E6CBA8", width=2)
        bbox = draw.textbbox((0, 0), loop_text, font=FONTS["body_small"])
        text_x = pill_x + (pill_w - (bbox[2] - bbox[0])) / 2
        text_y = pill_y + (pill_h - (bbox[3] - bbox[1])) / 2 - 2
        draw.text((text_x, text_y), loop_text, font=FONTS["body_small"], fill="#8A5A44")

        self.current_y = y0 + area_h + 18

    def add_table(self, headers: list[str], rows: list[list[str]], col_widths: list[int], header_fill: str = "#EAF2F8") -> None:
        draw = self.draw
        assert len(headers) == len(col_widths) == len(rows[0])
        cell_pad_x = 16
        cell_pad_y = 12
        row_heights: list[int] = []
        row_lines: list[list[list[str]]] = []
        for row in rows:
            line_groups = []
            max_lines = 1
            for cell, width in zip(row, col_widths):
                lines = wrap_paragraph(draw, cell, FONTS["body_small"], width - 2 * cell_pad_x)
                if not lines:
                    lines = [""]
                line_groups.append(lines)
                max_lines = max(max_lines, len(lines))
            row_lines.append(line_groups)
            row_heights.append(max_lines * font_line_height(FONTS["body_small"]) + 2 * cell_pad_y)

        header_height = font_line_height(FONTS["table_head"]) + 2 * cell_pad_y
        table_height = header_height + sum(row_heights) + len(rows) + 2
        self.ensure_space(table_height + 20)

        x0 = self.content_x
        y = self.current_y
        total_w = sum(col_widths)

        draw.rounded_rectangle((x0, y, x0 + total_w, y + header_height), radius=12, fill=header_fill, outline="#CBD5E1", width=2)
        x = x0
        for header, width in zip(headers, col_widths):
            draw.text((x + cell_pad_x, y + cell_pad_y - 2), header, font=FONTS["table_head"], fill="#1D3557")
            x += width

        y += header_height + 2
        for idx, (row, height, line_groups) in enumerate(zip(rows, row_heights, row_lines)):
            fill = "#FFFFFF" if idx % 2 == 0 else "#F8FBFE"
            draw.rectangle((x0, y, x0 + total_w, y + height), fill=fill, outline="#D7E0EA", width=1)
            x = x0
            for cell, width, lines in zip(row, col_widths, line_groups):
                cell_text = "\n".join(lines)
                draw.multiline_text((x + cell_pad_x, y + cell_pad_y - 1), cell_text, font=FONTS["body_small"], fill="#2B2F33", spacing=8)
                draw.line((x + width, y, x + width, y + height), fill="#D7E0EA", width=1)
                x += width
            y += height + 1
        self.current_y = y + 12

    def draw_footer(self) -> None:
        total_pages = len(self.pages)
        for idx, (img, draw) in enumerate(zip(self.pages, self.draws), start=1):
            footer_y = self.page_h - 48
            draw.line((self.margin_x, footer_y - 16, self.page_w - self.margin_x, footer_y - 16), fill="#CBD5E1", width=1)
            footer_text = f"{idx} / {total_pages}"
            bbox = draw.textbbox((0, 0), footer_text, font=FONTS["body_tiny"])
            tw = bbox[2] - bbox[0]
            draw.text((self.page_w - self.margin_x - tw, footer_y - 2), footer_text, font=FONTS["body_tiny"], fill="#6B7280")
            draw.text((self.margin_x, footer_y - 2), "日元的镜像", font=FONTS["body_tiny"], fill="#6B7280")

    def save_pdf(self, path: Path) -> None:
        self.draw_footer()
        rgb_pages = [img.convert("RGB") for img in self.pages]
        rgb_pages[0].save(path, save_all=True, append_images=rgb_pages[1:], resolution=150.0)


PAGE_W = 1240
PAGE_H = 1754


def build_report() -> ReportCanvas:
    r = ReportCanvas(PAGE_W, PAGE_H)
    r.pages.clear()
    r.draws.clear()
    r.add_title_page()

    # Page 2: framework + rupture mechanism.
    r._new_body_page()
    r.add_section_title("一、分析框架：为什么流动性更容易流向资产")
    r.add_paragraph(
        "在现代信用货币体系里，流动性扩张并不会平均流向所有部门，而是优先流向抵押品充足、估值清晰、变现迅速的资产。"
        "相比机器设备和研发投入，房地产与股票更容易承接大规模信贷，因此宽松货币并不必然提升实体生产率，却很容易通过杠杆进入资产市场。"
    )
    r.add_bullet_list(
        [
            "银行放贷天然偏好可抵押、可估值、可快速出售的资产，房地产和股票因此更具融资吸引力。",
            "当增量信贷流入资产池后，价格上涨会抬高抵押品价值，抵押品升值又会反过来支持更多授信。",
            "资产价格上涨、抵押品升值、信贷扩张和再上涨会形成反身性循环，这是泡沫最常见的生成机制。",
        ]
    )

    r.add_section_title("二、泡沫破裂：政策急刹车如何触发踩踏")
    r.add_paragraph(
        "依赖信贷扩张的泡沫，最大的弱点就是对融资条件极度敏感。一旦利率上升，或者新增信贷枯竭，资产持有者的现金流就会迅速恶化。"
        "1989年起，日本央行开始连续加息；1990年初，大藏省推出房地产贷款总量限制，直接切断房地产部门的新增信用供给。"
    )
    r.add_bullet_list(
        [
            "融资成本上升，杠杆持有者的现金流压力迅速加大。",
            "新增信贷被掐断后，资产持有者只能抛售股票和土地套现。",
            "资产价格下跌导致抵押品价值缩水，银行担心坏账而抽贷。",
            "抽贷又迫使企业进一步出售资产，形成典型的死亡螺旋。",
        ]
    )
    r.add_flow_diagram(
        "信用 - 抵押品闭环",
        ["宽松货币", "银行放贷扩张", "地产 / 股市上涨", "抵押品升值", "再授信扩张"],
        "这一闭环会把资产价格变化放大成信用扩张，反过来又把信用扩张推回资产价格。",
    )

    # Page 3: timeline + policy evolution.
    r._new_body_page()
    r.add_subsection_title("时间线一：1985-1990年泡沫形成")
    timeline_rows = [
        ["1985年9月", "《广场协议》签署，日元快速升值，日本出口部门承压。"],
        ["1986-1987年", "日本央行连续降息，官方贴现率降至2.5%，信用开始明显扩张。"],
        ["1987-1989年", "金融自由化推进，银行信用加速流向房地产和股市，土地成为核心抵押品。"],
        ["1989年12月29日", "日经225收于38,915.87点，泡沫资产价格达到高点之一。"],
        ["1989年5月-1990年8月", "日本央行连续加息5次，官方贴现率升至6.0%。"],
        ["1990年初", "大藏省实施房地产贷款总量限制，地产信用被直接收紧。"],
        ["1991年", "地价开始进入持续下行通道，泡沫转入去杠杆。"],
    ]
    r.add_table(["时间", "关键事件与含义"], timeline_rows, [160, r.content_w - 160])

    r.add_section_title("三、为何救不回来：资产负债表衰退")
    r.add_paragraph(
        "泡沫破裂后，日本进入资产负债表衰退。资产端大幅缩水，但负债端不会自动消失，于是企业和家庭的首要目标从“扩大收益”转为“尽快还债”。"
        "这意味着，即便央行把利率压到零，甚至进入负利率、量化宽松和收益率曲线控制，私人部门也未必愿意重新新增借贷。"
    )
    policy_rows = [
        ["1999年2月", "零利率政策（ZIRP）启动。"],
        ["2001年3月19日", "量化宽松（QE）启动，操作目标转向央行账户余额。"],
        ["2013年4月4日", "量化和质化宽松（QQE）推出。"],
        ["2016年1月29日", "负利率政策启动，部分超额准备金适用-0.1%。"],
        ["2016年9月21日", "收益率曲线控制（YCC）推出，10年期国债收益率目标约为0%。"],
    ]
    r.add_table(["时间", "政策含义"], policy_rows, [170, r.content_w - 170])
    r.add_paragraph(
        "这些政策说明了一件事：流动性可以被创造，但私人部门的借贷意愿不能被行政命令恢复。货币政策能压低融资成本，却未必能强迫家庭和企业重新冒险加杠杆。"
    )

    # Page 4: spillover + chart suggestions.
    r._new_body_page()
    r.add_section_title("四、日元的外溢：从国内货币到全球融资货币")
    r.add_paragraph(
        "当日本本土长期缺乏强劲信贷需求、利率长期维持低位时，日元的角色开始变化。它不再只是日本国内刺激经济的工具，而逐渐成为全球金融市场的重要融资货币。"
    )
    r.add_bullet_list(
        [
            "典型路径是日元套息交易：低成本借入日元，再兑换成美元或其他高收益货币，投入更高收益的风险资产。",
            "日元融资不是全球资产上涨的唯一原因，但它是非常重要的边际杠杆来源。",
            "日本央行一旦边际收紧，或者日元意外升值，套息仓位就可能被迫平仓，回撤会被迅速放大。",
        ]
    )
    r.add_box(
        "传导链条",
        [
            "低利率借入日元 -> 换汇 -> 买入高收益资产 -> 收益和杠杆同时放大 -> 条件反转时集中平仓。",
        ],
        fill="#FFF9F2",
        outline="#E6CBA8",
        title_color="#8A5A44",
    )

    r.add_section_title("五、图表建议")
    r.add_numbered_list(
        [
            "时间线图：横轴为1985-1991年，标注《广场协议》、连续降息、连续加息、房地产贷款总量限制和资产价格拐点。",
            "双轴折线图：左轴为日本官方贴现率，右轴为日经225指数，突出宽松期上涨与紧缩期回撤的对应关系。",
            "双轴折线图：左轴为政策利率，右轴为地价指数，说明房地产是信用循环的核心抵押品。",
            "政策演进图：串联1999年ZIRP、2001年QE、2013年QQE、2016年负利率与YCC，展示非常规货币政策的连续升级。",
            "机制框图：展示“借入日元 - 换汇 - 买入高收益资产 - 回撤时平仓”的套息交易链条。",
        ]
    )

    # Page 5: data, conclusion, sources.
    r._new_body_page()
    r.add_section_title("六、关键数据点")
    data_rows = [
        ["1986-1987年", "日本央行连续降息，官方贴现率降至2.5%。", "信用扩张开始明显加速。"],
        ["1989年12月29日", "日经225收于38,915.87点。", "泡沫资产价格达到标志性高点。"],
        ["1989年5月-1990年8月", "日本央行连续加息5次，官方贴现率升至6.0%。", "融资成本快速抬升。"],
        ["1990年初", "大藏省实施房地产贷款总量限制。", "地产新增信用被直接收紧。"],
        ["1991年", "地价开始进入持续下行通道。", "泡沫由价格回落转入去杠杆。"],
        ["1999年2月", "零利率政策启动。", "进入长期低利率时代。"],
        ["2001年3月19日", "量化宽松启动。", "货币政策转向资产负债表扩张。"],
        ["2016年9月21日", "收益率曲线控制推出。", "非常规政策进一步制度化。"],
    ]
    r.add_table(["时间", "数据点", "意义"], data_rows, [140, 470, r.content_w - 610])

    # Conclusion
    r.add_section_title("七、结论摘要")
    r.add_bullet_list(
        [
            "日本泡沫的本质，不是资产价格单独上涨，而是宽松流动性通过银行信贷和抵押品升值形成的正反馈闭环。",
            "泡沫破裂的直接原因，是货币政策收紧与房地产信用管制叠加，切断了信用扩张链条。",
            "泡沫破裂后，日本进入资产负债表衰退，私人部门去杠杆使货币宽松难以重新激活内生信用扩张。",
            "日元在这一背景下从国内货币转变为全球融资货币，套息交易成为其外溢机制。",
            "对当今全球资产泡沫而言，日元不是唯一源头，但它是重要的边际放大器，既能放大上行，也会在条件反转时放大回撤。",
        ]
    )

    r.add_section_title("来源说明")
    r.add_bullet_list(
        [
            "Bank of Japan: official policy rate history, ZIRP, QE, QQE, negative rate and YCC pages.",
            "Ministry of Land, Infrastructure, Transport and Tourism (Japan): land price survey and bubble-era land price materials.",
            "Nikkei Indexes: Nikkei 225 historical data and 1989 year-end high.",
            "Bank of Japan research notes on balance sheet recession, bank lending and carry-trade related transmission.",
        ],
        font=FONTS["body_small"],
        spacing=6,
    )

    return r


def main() -> None:
    report = build_report()
    report.save_pdf(PDF_PATH)

    # Also export page previews for visual inspection.
    for idx, page in enumerate(report.pages, start=1):
        preview_path = TMP_DIR / f"page_{idx:02d}.png"
        page.save(preview_path)

    print(PDF_PATH)
    for idx in range(1, len(report.pages) + 1):
        print(TMP_DIR / f"page_{idx:02d}.png")


if __name__ == "__main__":
    main()

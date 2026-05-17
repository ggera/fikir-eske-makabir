"""
build_text_pdf.py — ፍቅር እስከ መቃብር — formatted text PDF
=========================================================
Landscape A4, two columns per page.
Each .txt source file occupies exactly one column; no overflow.
555 source files → ceil(555/2) = 278 PDF pages.
"""

import argparse
import os
import re
from dataclasses import dataclass
from pathlib import Path
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

TEXT_DIR   = "ocr_text"
OUTPUT_PDF = "normalized-fikir-eske-makabir-text.pdf"
FONT_PATH  = "fonts/Geez_Manuscript_Zemen.ttf"
FONT_NAME  = "GeezManuscriptZemen"
REPO_ROOT   = Path(__file__).resolve().parent
COVER_IMAGE = REPO_ROOT / "cover2.jpg"
TOC_FILE    = "page_0006.txt"
SOURCE_PAGE_OFFSET = 2

TITLE  = "ፍቅር እስከ መቃብር"
AUTHOR = "ሀዲስ ዓለማየሁ"

C_TEXT   = HexColor("#1C1208")
C_HEADER = HexColor("#1C1208")
C_RULE   = HexColor("#B89A6A")
C_LABEL  = HexColor("#1C1208")
C_FOLIO  = HexColor("#5C3D1E")

PAGE_W, PAGE_H = landscape(A4)
L_MARGIN   = 1.2 * cm
R_MARGIN   = 1.2 * cm
TOP_MARGIN = 2.0 * cm
BOT_MARGIN = 1.4 * cm
GUTTER     = 0.8 * cm
COL_PAD    = 4.0

COL_W      = (PAGE_W - L_MARGIN - R_MARGIN - GUTTER) / 2
COL_X      = [L_MARGIN, L_MARGIN + COL_W + GUTTER]
COL_TOP    = PAGE_H - TOP_MARGIN
COL_BOT    = BOT_MARGIN
COL_TEXT_W = COL_W - 2 * COL_PAD

BODY_SIZE  = 10.5;  BODY_LEADING  = 17.5
H3_SIZE    = 12.5;  H3_LEADING    = 19.0
LABEL_SIZE =  9.0;  LABEL_LEADING = 13.5


@dataclass
class Block:
    kind: str
    text: str   = ""
    pts:  float = 0.0
    num:  str   = ""


def draw_decorations(c: Canvas, page_num: int) -> None:
    c.saveState()
    rule_y = PAGE_H - 1.55 * cm
    c.setStrokeColor(C_RULE); c.setLineWidth(0.75)
    c.line(L_MARGIN, rule_y, PAGE_W - R_MARGIN, rule_y)
    c.setFillColor(C_HEADER); c.setFont(FONT_NAME, 10.5)
    c.drawCentredString(PAGE_W / 2, rule_y + 5, TITLE)
    foot_y = BOT_MARGIN - 0.5 * cm
    c.setStrokeColor(C_RULE); c.setLineWidth(0.4)
    c.line(L_MARGIN, foot_y, PAGE_W - R_MARGIN, foot_y)
    c.setFillColor(C_FOLIO); c.setFont(FONT_NAME, 8.5)
    c.drawCentredString(PAGE_W / 2, foot_y - 10, str(page_num))
    c.setFont(FONT_NAME, 7.5); c.setFillColor(C_LABEL)
    c.drawString(L_MARGIN, foot_y - 10, AUTHOR)
    div_x = L_MARGIN + COL_W + GUTTER / 2
    c.setStrokeColor(C_RULE); c.setLineWidth(0.5)
    c.line(div_x, COL_BOT, div_x, PAGE_H - TOP_MARGIN + 0.35 * cm)
    c.restoreState()


def _word_wrap(c: Canvas, text: str, size: float) -> list:
    words = text.split()
    if not words:
        return [""]
    sp_w = c.stringWidth(" ", FONT_NAME, size)
    lines, cur, cur_w = [], [], 0.0
    for word in words:
        ww = c.stringWidth(word, FONT_NAME, size)
        needed = cur_w + (sp_w if cur else 0.0) + ww
        if cur and needed > COL_TEXT_W:
            lines.append(" ".join(cur)); cur, cur_w = [word], ww
        else:
            cur.append(word); cur_w = needed
    if cur:
        lines.append(" ".join(cur))
    return lines


class TwoColumnRenderer:
    """Pairs source files into landscape A4 pages (left col + right col).
    files[2n]   -> left  column of page n+1
    files[2n+1] -> right column of page n+1
    No overflow between columns. 555 files -> 278 pages.
    """

    def __init__(self, path: str) -> None:
        self._c = Canvas(path, pagesize=landscape(A4))
        self._c.setTitle(TITLE)
        self._c.setAuthor(AUTHOR)
        self._c.setSubject("ልቦለድ ታሪክ")
        self._page_num = 0

    def render_page(self, left_blocks: list, right_blocks: list) -> None:
        if self._page_num > 0:
            self._c.showPage()
        self._page_num += 1
        draw_decorations(self._c, self._page_num)
        self._render_column(left_blocks, col=0)
        if right_blocks:
            self._render_column(right_blocks, col=1)

    def _render_column(self, blocks: list, col: int) -> None:
        c       = self._c
        x       = COL_X[col] + COL_PAD
        right_x = COL_X[col] + COL_W - COL_PAD
        y       = COL_TOP

        def sl():
            return y - COL_BOT

        def space(pts):
            nonlocal y
            if sl() > pts:
                y -= pts

        def draw_line(text, size, leading, color):
            nonlocal y
            if sl() < leading:
                return
            c.setFont(FONT_NAME, size)
            c.setFillColor(color)
            c.drawString(x, y - size, text)
            y -= leading

        def draw_wrapped(text, size, leading, color):
            nonlocal y
            c.setFont(FONT_NAME, size)
            c.setFillColor(color)
            for line in _word_wrap(c, text, size):
                if sl() < leading:
                    return
                c.drawString(x, y - size, line)
                y -= leading

        def draw_toc_entry(title, num):
            nonlocal y
            if sl() < BODY_LEADING:
                return
            c.setFont(FONT_NAME, BODY_SIZE)
            c.setFillColor(C_TEXT)
            baseline = y - BODY_SIZE
            tw = c.stringWidth(title, FONT_NAME, BODY_SIZE)
            nw = c.stringWidth(num,   FONT_NAME, BODY_SIZE)
            dw = c.stringWidth(".",   FONT_NAME, BODY_SIZE)
            gap = (right_x - x) - tw - nw
            c.drawString(x, baseline, title)
            c.drawRightString(right_x, baseline, num)
            if gap > dw * 4:
                c.setFillColor(C_LABEL)
                c.drawString(x + tw + dw, baseline, "." * max(1, int((gap - dw * 2) / dw)))
            y -= BODY_LEADING

        for blk in blocks:
            if   blk.kind == "space":
                space(blk.pts)
            elif blk.kind == "h3":
                space(4)
                draw_wrapped(blk.text, H3_SIZE, H3_LEADING, C_HEADER)
                space(8)
            elif blk.kind == "body":
                draw_wrapped(blk.text, BODY_SIZE, BODY_LEADING, C_TEXT)
                space(0.5)
            elif blk.kind == "label":
                draw_line(blk.text, LABEL_SIZE, LABEL_LEADING, C_LABEL)
                space(2)
            elif blk.kind == "toc_entry":
                draw_toc_entry(blk.text, blk.num)
            elif blk.kind == "caption":
                col_cx = COL_X[col] + COL_W / 2
                col_my = (COL_TOP + COL_BOT) / 2
                c.setFont(FONT_NAME, H3_SIZE)
                c.setFillColor(C_TEXT)
                c.drawCentredString(col_cx, col_my, blk.text)
            elif blk.kind == "image":
                try:
                    ir = ImageReader(blk.text)
                    iw, ih = ir.getSize()
                    col_w_avail = right_x - x
                    col_h_avail = COL_TOP - COL_BOT
                    scale = min(col_w_avail / iw, col_h_avail / ih)
                    dw, dh = iw * scale, ih * scale
                    dx = x + (col_w_avail - dw) / 2
                    dy = (COL_TOP + COL_BOT) / 2 - dh / 2
                    c.drawImage(ir, dx, dy, width=dw, height=dh)
                except Exception:
                    pass

    def save(self) -> None:
        self._c.save()


_MARKDOWN_H3_RE = re.compile(r"^###\s+(.+)$")
_RAW_CHAPTER_RE = re.compile(r"^ም[እዕአ]ራፍ\b")
_TOC_ENTRY_RE   = re.compile(r"^(.+?)\s{2,}(\d+)\s*$")



def load_toc_title_map(text_dir: Path) -> dict:
    toc_path = text_dir / TOC_FILE
    if not toc_path.exists():
        return {}
    title_map = {}
    for raw_line in toc_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line == "ማውጫ":
            continue
        m = re.match(r"^(.*?)\s+(\d+)\s*$", line)
        if m:
            title_map[int(m.group(2)) + SOURCE_PAGE_OFFSET] = m.group(1).strip()
    return title_map


def _is_short_line(line: str, limit: int = 26) -> bool:
    return len(re.sub(r"\s+", "", line)) <= limit

def _is_chapter_line(line: str) -> bool:
    return bool(_RAW_CHAPTER_RE.match(line) or _MARKDOWN_H3_RE.match(line))

def _heading_from_line(line: str):
    m = _MARKDOWN_H3_RE.match(line)
    return m.group(1).strip() if m else None

def page_to_blocks(text: str, toc_title=None) -> list:
    blocks = []
    lines  = [ln.strip() for ln in text.splitlines()]
    para   = []

    def flush():
        if para:
            blocks.append(Block("body", " ".join(para)))
            para.clear()

    if toc_title:
        blocks.append(Block("space", pts=4))
        blocks.append(Block("h3", toc_title))
        blocks.append(Block("space", pts=8))

    non_empty = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if not toc_title and len(non_empty) == 1 and len(re.sub(r"\s+", "", non_empty[0])) <= 25:
        blocks.append(Block("caption", non_empty[0]))
        return blocks

    i = 0
    while i < len(lines):
        line = lines[i]
        if not line:
            flush()
            blocks.append(Block("space", pts=7))
            i += 1
            continue
        toc_m = _TOC_ENTRY_RE.match(line)
        if toc_m:
            flush()
            blocks.append(Block("toc_entry", text=toc_m.group(1).strip(), num=toc_m.group(2)))
            i += 1
            continue
        line = line.replace("\t", " ")
        if _is_chapter_line(line):
            flush()
            heading = _heading_from_line(line)
            if heading and heading != toc_title:
                blocks.append(Block("space", pts=4))
                blocks.append(Block("h3", heading))
                blocks.append(Block("space", pts=8))
            blocks.append(Block("space", pts=4))
            if heading is None:
                i += 1
                continue
            next_line = lines[i + 1] if i + 1 < len(lines) else ""
            if next_line and _is_short_line(next_line, 20):
                blocks.append(Block("label", next_line.replace("\t", " ")))
                i += 1
            blocks.append(Block("space", pts=8))
            i += 1
            continue
        para.append(line)
        i += 1

    flush()
    blocks.append(Block("space", pts=10))
    return blocks


def parse_args():
    p = argparse.ArgumentParser(description="Build the formatted text PDF.")
    p.add_argument("--text-dir",   default=TEXT_DIR)
    p.add_argument("--output-pdf", default=OUTPUT_PDF)
    p.add_argument("--font-path",  default=FONT_PATH)
    return p.parse_args()


def main():
    args = parse_args()

    def abs_path(s):
        p = Path(s)
        return p if p.is_absolute() else REPO_ROOT / p

    text_dir   = abs_path(args.text_dir)
    output_pdf = abs_path(args.output_pdf)
    font_path  = abs_path(args.font_path)

    pdfmetrics.registerFont(TTFont(FONT_NAME, str(font_path)))
    toc_map = load_toc_title_map(text_dir)
    files   = sorted(f for f in os.listdir(text_dir) if f.endswith(".txt"))
    total   = len(files)
    pages   = (total + 1) // 2
    print(f"Building text PDF from {total} source files → {pages} pages …")

    renderer = TwoColumnRenderer(str(output_pdf))
    for i in range(0, total, 2):
        left_fname  = files[i]
        right_fname = files[i + 1] if i + 1 < total else None
        left_text   = (text_dir / left_fname).read_text(encoding="utf-8")
        if i == 0 and COVER_IMAGE.exists():
            left_blocks = [Block("image", text=str(COVER_IMAGE))]
        else:
            left_blocks = page_to_blocks(left_text, toc_title=toc_map.get(i + 1))
        right_blocks = []
        if right_fname:
            right_text   = (text_dir / right_fname).read_text(encoding="utf-8")
            right_blocks = page_to_blocks(right_text, toc_title=toc_map.get(i + 2))
        renderer.render_page(left_blocks, right_blocks)
        print(f"  {min(i+2,total)}/{total}\r", end="", flush=True)

    renderer.save()
    print(f"\nDone → {output_pdf}")


if __name__ == "__main__":
    main()

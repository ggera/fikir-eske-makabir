"""
build_text_pdf.py — ፍቅር እስከ መቃብር — elegant modern text PDF
==============================================================
Portrait A4, one source page per PDF page.
Design: warm book palette · decorative header/footer.
"""

import argparse
import os
import re
from dataclasses import dataclass
from pathlib import Path
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

TEXT_DIR   = "ocr_text"
OUTPUT_PDF = "normalized-fikir-eske-makabir-text.pdf"
FONT_PATH  = "fonts/Geez_Manuscript_Zemen.ttf"
FONT_NAME  = "GeezManuscriptZemen"
REPO_ROOT  = Path(__file__).resolve().parent
TOC_FILE   = "page_0006.txt"
SOURCE_PAGE_OFFSET = 2

TITLE  = "ፍቅር እስከ መቃብር"
AUTHOR = "ሀዲስ ዓለማየሁ"

# ── Palette ──────────────────────────────────────────────────────────────
C_TEXT   = HexColor("#1C1208")
C_HEADER = HexColor("#3B2410")
C_RULE   = HexColor("#B89A6A")
C_LABEL  = HexColor("#7A5C35")
C_FOLIO  = HexColor("#5C3D1E")

# ── Page geometry ────────────────────────────────────────────────────────
PAGE_W, PAGE_H = A4                 # portrait: 595.28 × 841.89 pt
L_MARGIN   = 1.8 * cm
R_MARGIN   = 1.8 * cm
TOP_MARGIN = 2.0 * cm
BOT_MARGIN = 1.4 * cm
COL_PAD    = 3.0                    # inner horizontal padding (pt)

COL_TOP = PAGE_H - TOP_MARGIN
COL_BOT = BOT_MARGIN
TEXT_X  = L_MARGIN + COL_PAD
TEXT_W  = PAGE_W - L_MARGIN - R_MARGIN - 2 * COL_PAD

# ── Text metrics ─────────────────────────────────────────────────────────
BODY_SIZE    = 11.0;  BODY_LEADING    = 18.5
H3_SIZE      = 13.0;  H3_LEADING      = 20.0
LABEL_SIZE   =  9.5;  LABEL_LEADING   = 14.0


# ── Block types ───────────────────────────────────────────────────────────

@dataclass
class Block:
    kind: str        # 'body' | 'h3' | 'label' | 'space' | 'toc_entry'
    text: str = ""
    pts:  float = 0.0   # vertical space for 'space' blocks
    num:  str = ""      # page-number string for 'toc_entry' blocks


# ── Canvas decorations ────────────────────────────────────────────────────

def draw_decorations(c: Canvas, page_num: int) -> None:
    c.saveState()

    rule_y = PAGE_H - 1.55 * cm
    c.setStrokeColor(C_RULE)
    c.setLineWidth(0.75)
    c.line(L_MARGIN, rule_y, PAGE_W - R_MARGIN, rule_y)
    c.setFillColor(C_HEADER)
    c.setFont(FONT_NAME, 10.5)
    c.drawCentredString(PAGE_W / 2, rule_y + 5, TITLE)

    foot_y = BOT_MARGIN - 0.5 * cm
    c.setStrokeColor(C_RULE)
    c.setLineWidth(0.4)
    c.line(L_MARGIN, foot_y, PAGE_W - R_MARGIN, foot_y)
    c.setFillColor(C_FOLIO)
    c.setFont(FONT_NAME, 8.5)
    c.drawCentredString(PAGE_W / 2, foot_y - 10, str(page_num))
    c.setFont(FONT_NAME, 7.5)
    c.setFillColor(C_LABEL)
    c.drawString(L_MARGIN, foot_y - 10, AUTHOR)

    c.restoreState()


# ── Per-page renderer ─────────────────────────────────────────────────────

def _word_wrap(c: Canvas, text: str, size: float) -> list:
    """Split *text* into lines that fit within TEXT_W."""
    words = text.split()
    if not words:
        return [""]
    sp_w = c.stringWidth(" ", FONT_NAME, size)
    lines, cur, cur_w = [], [], 0.0
    for word in words:
        ww = c.stringWidth(word, FONT_NAME, size)
        needed = cur_w + (sp_w if cur else 0.0) + ww
        if cur and needed > TEXT_W:
            lines.append(" ".join(cur))
            cur, cur_w = [word], ww
        else:
            cur.append(word)
            cur_w = needed
    if cur:
        lines.append(" ".join(cur))
    return lines


class PageRenderer:
    """One PDF page per source text file; no cross-page text flow."""

    def __init__(self, path: str) -> None:
        self._c = Canvas(path, pagesize=A4)
        self._c.setTitle(TITLE)
        self._c.setAuthor(AUTHOR)
        self._c.setSubject("ልቦለድ ታሪክ")
        self._page_num = 0
        self._y = COL_TOP

    def new_page(self) -> None:
        """Advance to the next PDF page (called once per source file)."""
        if self._page_num > 0:
            self._c.showPage()
        self._page_num += 1
        self._y = COL_TOP
        draw_decorations(self._c, self._page_num)

    def _space_left(self) -> float:
        return self._y - COL_BOT

    def _set_font(self, size: float, color) -> None:
        self._c.setFont(FONT_NAME, size)
        self._c.setFillColor(color)

    def space(self, pts: float) -> None:
        if self._space_left() > pts:
            self._y -= pts

    def draw_line(self, text: str, size: float, leading: float, color) -> None:
        if self._space_left() < leading:
            return
        self._set_font(size, color)
        self._c.drawString(TEXT_X, self._y - size, text)
        self._y -= leading

    def draw_wrapped(self, text: str, size: float, leading: float, color) -> None:
        lines = _word_wrap(self._c, text, size)
        self._set_font(size, color)
        for line in lines:
            if self._space_left() < leading:
                return
            self._c.drawString(TEXT_X, self._y - size, line)
            self._y -= leading

    def draw_toc_entry(self, title: str, num: str) -> None:
        """Title flush-left, page number flush-right, dots in between."""
        if self._space_left() < BODY_LEADING:
            return
        c = self._c
        c.setFont(FONT_NAME, BODY_SIZE)
        c.setFillColor(C_TEXT)
        baseline  = self._y - BODY_SIZE
        right_x   = TEXT_X + TEXT_W
        title_w   = c.stringWidth(title, FONT_NAME, BODY_SIZE)
        num_w     = c.stringWidth(num,   FONT_NAME, BODY_SIZE)
        dot_w     = c.stringWidth(".",   FONT_NAME, BODY_SIZE)
        gap       = TEXT_W - title_w - num_w
        c.drawString(TEXT_X, baseline, title)
        c.drawRightString(right_x, baseline, num)
        if gap > dot_w * 4:
            n_dots  = max(1, int((gap - dot_w * 2) / dot_w))
            c.setFillColor(C_LABEL)
            c.drawString(TEXT_X + title_w + dot_w, baseline, "." * n_dots)
        self._y -= BODY_LEADING

    def render(self, blocks: list) -> None:
        for blk in blocks:
            if blk.kind == "space":
                self.space(blk.pts)
            elif blk.kind == "h3":
                self.space(4)
                self.draw_wrapped(blk.text, H3_SIZE, H3_LEADING, C_HEADER)
                self.space(8)
            elif blk.kind == "body":
                self.draw_wrapped(blk.text, BODY_SIZE, BODY_LEADING, C_TEXT)
                self.space(0.5)
            elif blk.kind == "label":
                self.draw_line(blk.text, LABEL_SIZE, LABEL_LEADING, C_LABEL)
                self.space(2)
            elif blk.kind == "toc_entry":
                self.draw_toc_entry(blk.text, blk.num)

    def save(self) -> None:
        self._c.save()


# ── Text → Block conversion ───────────────────────────────────────────────

_MARKDOWN_H3_RE = re.compile(r"^###\s+(.+)$")
_RAW_CHAPTER_RE = re.compile(r"^ም[እዕአ]ራፍ\b")
_TOC_ENTRY_RE   = re.compile(r"^(.*?)\t+(\d+)\s*$")
_STRONG_PUNCT   = ("።", "?", "!", "؟")


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


def _looks_like_verse_block(lines: list, index: int) -> bool:
    window, cursor = [], index
    while cursor < len(lines) and lines[cursor] and len(window) < 4:
        window.append(lines[cursor])
        cursor += 1
    if len(window) < 2:
        return False
    return sum(
        1 for ln in window
        if _is_short_line(ln, 24) and not ln.endswith(_STRONG_PUNCT)
    ) >= 2


def page_to_blocks(text: str, toc_title=None) -> list:
    """Convert one source page's text into a list of render Blocks."""
    blocks = []
    lines = [ln.strip() for ln in text.splitlines()]
    para = []

    def flush():
        if para:
            blocks.append(Block("body", " ".join(para)))
            para.clear()

    if toc_title:
        blocks.append(Block("space", pts=4))
        blocks.append(Block("h3", toc_title))
        blocks.append(Block("space", pts=8))

    i = 0
    while i < len(lines):
        line = lines[i]

        if not line:
            flush()
            blocks.append(Block("space", pts=7))
            i += 1
            continue

        # TOC entry: "title\t\t\tN" → flush-left title + flush-right number
        toc_m = _TOC_ENTRY_RE.match(line)
        if toc_m:
            flush()
            blocks.append(Block("toc_entry", text=toc_m.group(1).strip(), num=toc_m.group(2)))
            i += 1
            continue

        # Strip stray tabs from all other lines
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

        if _looks_like_verse_block(lines, i):
            flush()
            start_i = i
            while i < len(lines) and lines[i]:
                vline = lines[i].replace("\t", " ")
                if not (_is_short_line(vline, 24) and not vline.endswith(_STRONG_PUNCT)):
                    break
                blocks.append(Block("label", vline))
                i += 1
            if i == start_i:
                para.append(lines[i].replace("\t", " "))
                i += 1
            blocks.append(Block("space", pts=5))
            continue

        para.append(line)
        i += 1

    flush()
    blocks.append(Block("space", pts=10))
    return blocks


# ── CLI ───────────────────────────────────────────────────────────────────

def parse_args():
    p = argparse.ArgumentParser(description="Build the formatted text PDF from OCR text files.")
    p.add_argument("--text-dir",   default=TEXT_DIR,   help="OCR text directory.")
    p.add_argument("--output-pdf", default=OUTPUT_PDF, help="Output PDF path.")
    p.add_argument("--font-path",  default=FONT_PATH,  help="Ethiopic TTF font path.")
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
    print(f"Building text PDF from {total} source pages …")

    renderer = PageRenderer(str(output_pdf))
    for i, fname in enumerate(files):
        print(f"  {i + 1}/{total}\r", end="", flush=True)
        text   = (text_dir / fname).read_text(encoding="utf-8")
        blocks = page_to_blocks(text, toc_title=toc_map.get(i + 1))
        renderer.new_page()
        renderer.render(blocks)

    renderer.save()
    print(f"\nDone → {output_pdf}")


if __name__ == "__main__":
    main()


import argparse
import os
import re
from dataclasses import dataclass
from pathlib import Path
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

TEXT_DIR   = "ocr_text"
OUTPUT_PDF = "normalized-fikir-eske-makabir-text.pdf"
FONT_PATH  = "fonts/Geez_Manuscript_Zemen.ttf"
FONT_NAME  = "GeezManuscriptZemen"
REPO_ROOT = Path(__file__).resolve().parent
TOC_FILE = "page_0006.txt"
SOURCE_PAGE_OFFSET = 2

TITLE  = "ፍቅር እስከ መቃብር"
AUTHOR = "ሀዲስ ዓለማየሁ"

# ── Palette ──────────────────────────────────────────────────────────────
C_TEXT   = HexColor("#1C1208")
C_HEADER = HexColor("#3B2410")
C_RULE   = HexColor("#B89A6A")
C_LABEL  = HexColor("#7A5C35")
C_FOLIO  = HexColor("#5C3D1E")

# ── Page geometry ────────────────────────────────────────────────────────
PAGE_W, PAGE_H = landscape(A4)
L_MARGIN   = 1.0 * cm
R_MARGIN   = 0.4 * cm
TOP_MARGIN = 2.0 * cm
BOT_MARGIN = 1.4 * cm
GUTTER     = 0.8 * cm

COL_W   = (PAGE_W - L_MARGIN - R_MARGIN - GUTTER) / 2
COL_H   = PAGE_H - TOP_MARGIN - BOT_MARGIN
COL_PAD = 3.0                        # horizontal inner padding (pt)
COL_X   = [L_MARGIN, L_MARGIN + COL_W + GUTTER]
COL_TOP = PAGE_H - TOP_MARGIN        # canvas y of column top
COL_BOT = BOT_MARGIN                 # canvas y of column bottom
TEXT_W  = COL_W - 2 * COL_PAD       # usable text width inside a column

# ── Text metrics ─────────────────────────────────────────────────────────
BODY_SIZE    = 11.0;  BODY_LEADING    = 18.5
H3_SIZE      = 13.0;  H3_LEADING      = 18.0
LABEL_SIZE   =  9.0;  LABEL_LEADING   = 13.5


# ── Block types ───────────────────────────────────────────────────────────

@dataclass
class Block:
    kind: str        # 'body' | 'h3' | 'label' | 'space'
    text: str = ""
    pts: float = 0.0  # vertical space for 'space' blocks


# ── Canvas decorations ────────────────────────────────────────────────────

def draw_decorations(c: Canvas, page_num: int) -> None:
    c.saveState()

    rule_y = PAGE_H - 1.55 * cm
    c.setStrokeColor(C_RULE)
    c.setLineWidth(0.75)
    c.line(L_MARGIN, rule_y, PAGE_W - R_MARGIN, rule_y)
    c.setFillColor(C_HEADER)
    c.setFont(FONT_NAME, 10.5)
    c.drawCentredString(PAGE_W / 2, rule_y + 5, TITLE)

    foot_y = BOT_MARGIN - 0.5 * cm
    c.setStrokeColor(C_RULE)
    c.setLineWidth(0.4)
    c.line(L_MARGIN, foot_y, PAGE_W - R_MARGIN, foot_y)
    c.setFillColor(C_FOLIO)
    c.setFont(FONT_NAME, 8.5)
    c.drawCentredString(PAGE_W / 2, foot_y - 10, str(page_num))
    c.setFont(FONT_NAME, 7.5)
    c.setFillColor(C_LABEL)
    c.drawString(L_MARGIN, foot_y - 10, AUTHOR)

    div_x = L_MARGIN + COL_W + GUTTER / 2
    c.setStrokeColor(C_RULE)
    c.setLineWidth(0.5)
    c.line(div_x, COL_BOT, div_x, PAGE_H - TOP_MARGIN + 0.35 * cm)

    c.restoreState()


# ── Column-flow renderer ──────────────────────────────────────────────────

def _word_wrap(c: Canvas, text: str, size: float) -> list:
    """Split *text* into lines that fit within TEXT_W at *size*."""
    words = text.split()
    if not words:
        return [""]
    sp_w = c.stringWidth(" ", FONT_NAME, size)
    lines, cur, cur_w = [], [], 0.0
    for word in words:
        ww = c.stringWidth(word, FONT_NAME, size)
        needed = cur_w + (sp_w if cur else 0.0) + ww
        if cur and needed > TEXT_W:
            lines.append(" ".join(cur))
            cur, cur_w = [word], ww
        else:
            cur.append(word)
            cur_w = needed
    if cur:
        lines.append(" ".join(cur))
    return lines


class ColumnPager:
    """Streams content into left/right columns across landscape A4 pages."""

    def __init__(self, path: str) -> None:
        self._c = Canvas(path, pagesize=landscape(A4))
        self._c.setTitle(TITLE)
        self._c.setAuthor(AUTHOR)
        self._c.setSubject("ልቦለድ ታሪክ")
        self._page_num = 1
        self._col = 0
        self._y = COL_TOP
        self._col_has_content = False
        draw_decorations(self._c, self._page_num)

    # ── Navigation ────────────────────────────────────────────────────────

    def _space_left(self) -> float:
        return self._y - COL_BOT

    def _advance(self) -> None:
        if self._col == 0:
            self._col = 1
        else:
            self._c.showPage()
            self._page_num += 1
            self._col = 0
            draw_decorations(self._c, self._page_num)
        self._y = COL_TOP
        self._col_has_content = False

    @property
    def _x(self) -> float:
        return COL_X[self._col] + COL_PAD

    # ── Drawing primitives ────────────────────────────────────────────────

    def _set_font(self, size: float, color) -> None:
        self._c.setFont(FONT_NAME, size)
        self._c.setFillColor(color)

    def space(self, pts: float) -> None:
        if self._col_has_content and self._space_left() > pts:
            self._y -= pts

    def draw_line(self, text: str, size: float, leading: float, color) -> None:
        if self._space_left() < leading:
            self._advance()
        self._set_font(size, color)
        self._c.drawString(self._x, self._y - size, text)
        self._y -= leading
        self._col_has_content = True

    def draw_wrapped(self, text: str, size: float, leading: float, color) -> None:
        lines = _word_wrap(self._c, text, size)
        self._set_font(size, color)
        for line in lines:
            if self._space_left() < leading:
                self._advance()
                self._set_font(size, color)
            self._c.drawString(self._x, self._y - size, line)
            self._y -= leading
            self._col_has_content = True

    # ── Block renderer ────────────────────────────────────────────────────

    def render(self, blocks: list) -> None:
        for blk in blocks:
            if blk.kind == "space":
                self.space(blk.pts)
            elif blk.kind == "h3":
                self.space(4)
                self.draw_wrapped(blk.text, H3_SIZE, H3_LEADING, C_HEADER)
                self.space(8)
            elif blk.kind == "body":
                self.draw_wrapped(blk.text, BODY_SIZE, BODY_LEADING, C_TEXT)
                self.space(0.5)
            elif blk.kind == "label":
                self.draw_line(blk.text, LABEL_SIZE, LABEL_LEADING, C_LABEL)
                self.space(2)

    def save(self) -> None:
        self._c.save()


# ── Text → Block conversion ───────────────────────────────────────────────

_MARKDOWN_H3_RE = re.compile(r"^###\s+(.+)$")
_RAW_CHAPTER_RE = re.compile(r"^ም[እዕአ]ራፍ\b")
_STRONG_PUNCT   = ("።", "?", "!", "؟")


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


def _looks_like_verse_block(lines: list, index: int) -> bool:
    window, cursor = [], index
    while cursor < len(lines) and lines[cursor] and len(window) < 4:
        window.append(lines[cursor])
        cursor += 1
    if len(window) < 2:
        return False
    return sum(
        1 for ln in window
        if _is_short_line(ln, 24) and not ln.endswith(_STRONG_PUNCT)
    ) >= 2


def page_to_blocks(text: str, toc_title=None) -> list:
    """Convert one source page's text into a list of render Blocks."""
    blocks = []
    lines = [ln.strip() for ln in text.splitlines()]
    para = []

    def flush():
        if para:
            blocks.append(Block("body", " ".join(para)))
            para.clear()

    if toc_title:
        blocks.append(Block("space", pts=4))
        blocks.append(Block("h3", toc_title))
        blocks.append(Block("space", pts=8))

    i = 0
    while i < len(lines):
        line = lines[i]

        if not line:
            flush()
            blocks.append(Block("space", pts=7))
            i += 1
            continue

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
                blocks.append(Block("label", next_line))
                i += 1
            blocks.append(Block("space", pts=8))
            i += 1
            continue

        if _looks_like_verse_block(lines, i):
            flush()
            start_i = i
            while i < len(lines) and lines[i]:
                vline = lines[i]
                if not (_is_short_line(vline, 24) and not vline.endswith(_STRONG_PUNCT)):
                    break
                blocks.append(Block("label", vline))
                i += 1
            if i == start_i:
                # First line wasn't verse-like; treat as body to avoid infinite loop
                para.append(lines[i])
                i += 1
            blocks.append(Block("space", pts=5))
            continue

        para.append(line)
        i += 1

    flush()
    blocks.append(Block("space", pts=10))
    return blocks


# ── CLI ───────────────────────────────────────────────────────────────────

def parse_args():
    p = argparse.ArgumentParser(description="Build the formatted text PDF from OCR text files.")
    p.add_argument("--text-dir",   default=TEXT_DIR,   help="OCR text directory.")
    p.add_argument("--output-pdf", default=OUTPUT_PDF, help="Output PDF path.")
    p.add_argument("--font-path",  default=FONT_PATH,  help="Ethiopic TTF font path.")
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
    print(f"Building text PDF from {total} source pages …")

    pager = ColumnPager(str(output_pdf))
    for i, fname in enumerate(files):
        print(f"  {i + 1}/{total}\r", end="", flush=True)
        text   = (text_dir / fname).read_text(encoding="utf-8")
        blocks = page_to_blocks(text, toc_title=toc_map.get(i + 1))
        pager.render(blocks)

    pager.save()
    print(f"\nDone → {output_pdf}")


if __name__ == "__main__":
    main()

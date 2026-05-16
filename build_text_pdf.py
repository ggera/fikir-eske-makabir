"""
build_text_pdf.py — ፍቅር እስከ መቃብር — elegant modern text PDF
==============================================================
Landscape A4, two original pages per PDF spread.
Design: warm book palette · decorative header/footer · column rule.
"""

import argparse
import os
import re
from pathlib import Path
from reportlab.platypus import BaseDocTemplate, PageTemplate, Frame, \
    Paragraph, Spacer
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_LEFT
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

TEXT_DIR   = "ocr_text"
OUTPUT_PDF = "hadis_text.pdf"
FONT_PATH  = "fonts/Geez_Manuscript_Zemen.ttf"
FONT_NAME  = "GeezManuscriptZemen"
REPO_ROOT = Path(__file__).resolve().parent

TITLE  = "ፍቅር እስከ መቃብር"
AUTHOR = "ሀዲስ ዓለማየሁ"

# ── Palette ──────────────────────────────────────────────────────────────
C_TEXT   = HexColor("#1C1208")   # warm near-black
C_HEADER = HexColor("#3B2410")   # deep espresso brown
C_RULE   = HexColor("#B89A6A")   # antique gold
C_LABEL  = HexColor("#7A5C35")   # medium amber
C_FOLIO  = HexColor("#5C3D1E")   # dark amber

# ── Page geometry ────────────────────────────────────────────────────────
PAGE_W, PAGE_H = landscape(A4)   # 841.89 × 595.28 pt
L_MARGIN   = 1.0 * cm
R_MARGIN   = 0.4 * cm
TOP_MARGIN = 2.0 * cm           # sits below decorative header
BOT_MARGIN = 1.4 * cm           # sits above decorative footer
GUTTER     = 0.8 * cm

COL_W = (PAGE_W - L_MARGIN - R_MARGIN - GUTTER) / 2
COL_H = PAGE_H - TOP_MARGIN - BOT_MARGIN


# ── Canvas decorations ───────────────────────────────────────────────────

def draw_decorations(canvas, doc):
    """Header bar, footer bar, and column divider on every page."""
    canvas.saveState()

    # Header rule + title
    rule_y = PAGE_H - 1.55 * cm
    canvas.setStrokeColor(C_RULE)
    canvas.setLineWidth(0.75)
    canvas.line(L_MARGIN, rule_y, PAGE_W - R_MARGIN, rule_y)

    canvas.setFillColor(C_HEADER)
    canvas.setFont(FONT_NAME, 10.5)
    canvas.drawCentredString(PAGE_W / 2, rule_y + 5, TITLE)

    # Footer rule + page number + author
    foot_rule_y = BOT_MARGIN - 0.5 * cm
    canvas.setStrokeColor(C_RULE)
    canvas.setLineWidth(0.4)
    canvas.line(L_MARGIN, foot_rule_y, PAGE_W - R_MARGIN, foot_rule_y)

    canvas.setFillColor(C_FOLIO)
    canvas.setFont(FONT_NAME, 8.5)
    canvas.drawCentredString(PAGE_W / 2, foot_rule_y - 10, str(doc.page))

    canvas.setFont(FONT_NAME, 7.5)
    canvas.setFillColor(C_LABEL)
    canvas.drawString(L_MARGIN, foot_rule_y - 10, AUTHOR)

    # Vertical column divider
    div_x = L_MARGIN + COL_W + GUTTER / 2
    canvas.setStrokeColor(C_RULE)
    canvas.setLineWidth(0.5)
    canvas.line(div_x, BOT_MARGIN, div_x, PAGE_H - TOP_MARGIN + 0.35 * cm)

    canvas.restoreState()


# ── Page template ────────────────────────────────────────────────────────

def make_page_template():
    pad = 3   # inner column padding (pt)
    left_frame = Frame(
        L_MARGIN, BOT_MARGIN,
        COL_W, COL_H,
        leftPadding=pad, rightPadding=pad,
        topPadding=4, bottomPadding=2,
        id="left",
    )
    right_frame = Frame(
        L_MARGIN + COL_W + GUTTER, BOT_MARGIN,
        COL_W, COL_H,
        leftPadding=pad, rightPadding=pad,
        topPadding=4, bottomPadding=2,
        id="right",
    )
    return PageTemplate(
        id="two_col",
        frames=[left_frame, right_frame],
        onPage=draw_decorations,
    )


# ── Content helpers ───────────────────────────────────────────────────────

_CHAPTER_RE = re.compile(r"^ምእራፍ\s+\d+")
_STRONG_PUNCT = ("።", "?", "!", "؟")


def _is_short_line(line: str, limit: int = 26) -> bool:
    compact = re.sub(r"\s+", "", line)
    return len(compact) <= limit


def _is_chapter_line(line: str) -> bool:
    return bool(_CHAPTER_RE.match(line))


def _looks_like_verse_block(lines, index: int) -> bool:
    window = []
    cursor = index
    while cursor < len(lines) and lines[cursor] and len(window) < 4:
        window.append(lines[cursor])
        cursor += 1

    if len(window) < 2:
        return False

    short_unpunctuated = sum(
        1 for line in window
        if _is_short_line(line, 24) and not line.endswith(_STRONG_PUNCT)
    )
    return short_unpunctuated >= 2


def _emit_paragraph(elems, paragraph_lines, body_style):
    if paragraph_lines:
        elems.append(Paragraph(" ".join(paragraph_lines), body_style))
        paragraph_lines.clear()

def page_elements(page_num, text, body_style, label_style):
    """Flowables for one original page."""
    elems = []
    safe = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    lines = [raw_line.strip() for raw_line in safe.splitlines()]
    paragraph_lines = []
    index = 0
    while index < len(lines):
        line = lines[index]

        if not line:
            _emit_paragraph(elems, paragraph_lines, body_style)
            elems.append(Spacer(1, 7))
            index += 1
            continue

        if _is_chapter_line(line):
            _emit_paragraph(elems, paragraph_lines, body_style)
            elems.append(Spacer(1, 4))
            elems.append(Paragraph(line, label_style))
            next_line = lines[index + 1] if index + 1 < len(lines) else ""
            if next_line and _is_short_line(next_line, 20):
                elems.append(Paragraph(next_line, label_style))
                index += 1
            elems.append(Spacer(1, 8))
            index += 1
            continue

        if _looks_like_verse_block(lines, index):
            _emit_paragraph(elems, paragraph_lines, body_style)
            while index < len(lines) and lines[index]:
                verse_line = lines[index]
                if not (_is_short_line(verse_line, 24) and not verse_line.endswith(_STRONG_PUNCT)):
                    break
                elems.append(Paragraph(verse_line, label_style))
                index += 1
            elems.append(Spacer(1, 5))
            continue

        paragraph_lines.append(line)
        index += 1

    _emit_paragraph(elems, paragraph_lines, body_style)
    elems.append(Spacer(1, 10))
    return elems


# ── Main ──────────────────────────────────────────────────────────────────

def parse_args():
    parser = argparse.ArgumentParser(description="Build the formatted text PDF from OCR text files.")
    parser.add_argument(
        "--text-dir",
        default=TEXT_DIR,
        help=f"Directory containing per-page OCR text files. Defaults to {TEXT_DIR}.",
    )
    parser.add_argument(
        "--output-pdf",
        default=OUTPUT_PDF,
        help=f"Output PDF path. Defaults to {OUTPUT_PDF}.",
    )
    parser.add_argument(
        "--font-path",
        default=FONT_PATH,
        help=f"Path to the Ethiopic font file. Defaults to {FONT_PATH}.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    text_dir = Path(args.text_dir)
    if not text_dir.is_absolute():
        text_dir = REPO_ROOT / text_dir

    output_pdf = Path(args.output_pdf)
    if not output_pdf.is_absolute():
        output_pdf = REPO_ROOT / output_pdf

    font_path = Path(args.font_path)
    if not font_path.is_absolute():
        font_path = REPO_ROOT / font_path

    pdfmetrics.registerFont(TTFont(FONT_NAME, str(font_path)))

    body_style = ParagraphStyle(
        "body",
        fontName=FONT_NAME,
        fontSize=11,
        leading=18.5,
        alignment=TA_JUSTIFY,
        spaceAfter=0.5,
        textColor=C_TEXT,
        splitLongWords=False,
    )
    label_style = ParagraphStyle(
        "label",
        fontName=FONT_NAME,
        fontSize=9,
        leading=13.5,
        alignment=TA_LEFT,
        textColor=C_LABEL,
        spaceAfter=2,
    )

    files = sorted(f for f in os.listdir(text_dir) if f.endswith(".txt"))
    total = len(files)
    print(f"Building 2-up text PDF from {total} pages ...")

    doc = BaseDocTemplate(
        str(output_pdf),
        pagesize=landscape(A4),
        leftMargin=L_MARGIN,
        rightMargin=R_MARGIN,
        topMargin=TOP_MARGIN,
        bottomMargin=BOT_MARGIN,
        title=TITLE,
        author=AUTHOR,
        subject="ልቦለድ ታሪክ",
    )
    doc.addPageTemplates([make_page_template()])

    story = []
    for i, fname in enumerate(files):
        print(f"  Page {i + 1}/{total} ...", end="\r")
        text = open(text_dir / fname, encoding="utf-8").read()
        story.extend(page_elements(i + 1, text, body_style, label_style))

    doc.build(story)
    print(f"\nDone! Output: {output_pdf}")


if __name__ == "__main__":
    main()

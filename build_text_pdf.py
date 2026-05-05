"""
build_text_pdf.py — Build a clean, readable text-only PDF from ocr_text/*.txt
==============================================================================
Uses the Kefa III font (macOS built-in Ethiopic font) to render all 280 pages
of cleaned Amharic text into a properly readable PDF.

Output: hadis_text.pdf
"""

import os
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm

TEXT_DIR   = "ocr_text"
OUTPUT_PDF = "hadis_text.pdf"
FONT_PATH  = "/System/Library/Fonts/Supplemental/KefaIII.ttf"
FONT_NAME  = "Kefa"

PAGE_W, PAGE_H = A4
MARGIN_X = 2.5 * cm
MARGIN_Y = 2.5 * cm
FONT_SIZE   = 13
LINE_HEIGHT = FONT_SIZE * 1.6
TEXT_WIDTH  = PAGE_W - 2 * MARGIN_X
MAX_Y       = PAGE_H - MARGIN_Y
START_Y     = PAGE_H - MARGIN_Y - FONT_SIZE


def wrap_line(c, text, max_width):
    """Split a line into sub-lines that fit within max_width."""
    words = text.split(" ")
    lines = []
    current = ""
    for word in words:
        test = (current + " " + word).strip()
        if c.stringWidth(test, FONT_NAME, FONT_SIZE) <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines if lines else [""]


def main():
    pdfmetrics.registerFont(TTFont(FONT_NAME, FONT_PATH))

    files = sorted(f for f in os.listdir(TEXT_DIR) if f.endswith(".txt"))
    total = len(files)
    print(f"Building text PDF from {total} pages ...")

    c = canvas.Canvas(OUTPUT_PDF, pagesize=A4)
    c.setFont(FONT_NAME, FONT_SIZE)

    for i, fname in enumerate(files):
        print(f"  Page {i + 1}/{total} ...", end="\r")
        text = open(os.path.join(TEXT_DIR, fname), encoding="utf-8").read()

        # Page number header
        c.setFont(FONT_NAME, 9)
        c.setFillColorRGB(0.5, 0.5, 0.5)
        c.drawRightString(PAGE_W - MARGIN_X, PAGE_H - MARGIN_Y + 0.3 * cm,
                          f"— {i + 1} —")

        c.setFont(FONT_NAME, FONT_SIZE)
        c.setFillColorRGB(0, 0, 0)

        y = START_Y
        for raw_line in text.splitlines():
            wrapped = wrap_line(c, raw_line.strip(), TEXT_WIDTH)
            for sub in wrapped:
                if y < MARGIN_Y:
                    c.showPage()
                    c.setFont(FONT_NAME, FONT_SIZE)
                    c.setFillColorRGB(0, 0, 0)
                    y = START_Y
                # Right-align for RTL Ethiopic text
                c.drawRightString(PAGE_W - MARGIN_X, y, sub)
                y -= LINE_HEIGHT
            y -= LINE_HEIGHT * 0.2  # small paragraph gap between original lines

        c.showPage()

    c.save()
    print(f"\nDone! Output: {OUTPUT_PDF}")


if __name__ == "__main__":
    main()

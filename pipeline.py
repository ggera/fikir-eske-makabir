"""
pipeline.py — Hadis OCR Pipeline
=================================
Converts a scanned Amharic PDF to a searchable PDF,
replacing all Ethiopic word separators ፡ (U+1361) with spaces.

Usage:
    python3 pipeline.py

Output:
    hadis_clean.pdf  — searchable PDF with ፡ replaced by spaces
    ocr_text/        — per-page plain text files (for inspection)
"""

import os
import sys
import fitz           # pymupdf
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import io

# ── Config ───────────────────────────────────────────────────────────────
INPUT_PDF   = "hadis_original.pdf"
OUTPUT_PDF  = "hadis_clean.pdf"
TEXT_DIR    = "ocr_text"
DPI         = 300          # Higher = better OCR accuracy, slower
LANG        = "amh"        # Tesseract Amharic language pack
SEPARATOR   = "\u1361"     # ፡  Ethiopic wordspace
REPLACEMENT = " "          # Replace with plain space
# ─────────────────────────────────────────────────────────────────────────

os.makedirs(TEXT_DIR, exist_ok=True)


def ocr_page(image: Image.Image) -> str:
    """Run Tesseract OCR on a PIL image, return cleaned text."""
    raw = pytesseract.image_to_string(image, lang=LANG)
    return raw.replace(SEPARATOR, REPLACEMENT)


def build_pdf(images, texts, output_path):
    """
    Build a PDF where each page is the original scan image
    with an invisible text layer on top (searchable PDF).
    """
    doc = fitz.open()

    for i, (img, text) in enumerate(zip(images, texts)):
        print(f"  Building page {i + 1}/{len(images)} ...", end="\r")

        # Convert PIL image → bytes
        img_bytes = io.BytesIO()
        img.save(img_bytes, format="PNG")
        img_bytes.seek(0)

        # Insert image as a full-page PDF page
        img_pdf_bytes = fitz.open("png", img_bytes.read())
        rect = img_pdf_bytes[0].rect
        page = doc.new_page(width=rect.width, height=rect.height)
        page.insert_image(rect, stream=img_bytes.getvalue())

        # Overlay invisible text layer
        # (font size 1, white on white — makes it selectable/searchable)
        tw = fitz.TextWriter(page.rect)
        try:
            font = fitz.Font("helv")
            tw.append((0, 10), text, font=font, fontsize=1)
            tw.write_text(page, color=(1, 1, 1), opacity=0)
        except Exception:
            pass  # If text layer fails, page still has the image

    doc.save(output_path, garbage=4, deflate=True)
    doc.close()
    print(f"\n  Saved: {output_path}")


def already_done(page_num: int) -> bool:
    """Return True if this 1-based page has already been OCR'd."""
    return os.path.exists(os.path.join(TEXT_DIR, f"page_{page_num:04d}.txt"))


def main():
    # Determine total pages without loading all images first
    doc = fitz.open(INPUT_PDF)
    total = doc.page_count
    doc.close()
    print(f"      {total} pages in PDF.")

    # Find first page that still needs OCR
    first_todo = next((p for p in range(1, total + 1) if not already_done(p)), None)

    if first_todo is None:
        print("      All pages already OCR'd — skipping to PDF build step.")
    else:
        print(f"[2/3] Running Tesseract OCR (lang={LANG}), resuming from page {first_todo} ...")
        print(f"[1/3] Converting pages {first_todo}–{total} to images at {DPI} DPI ...")
        images_todo = convert_from_path(INPUT_PDF, dpi=DPI, first_page=first_todo, last_page=total)

        for idx, img in enumerate(images_todo):
            page_num = first_todo + idx
            print(f"      Page {page_num}/{total} ...", end="\r")
            text = ocr_page(img)
            txt_path = os.path.join(TEXT_DIR, f"page_{page_num:04d}.txt")
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(text)
        print(f"\n      OCR complete. Text saved to '{TEXT_DIR}/'")

    # Load all texts from disk for PDF build
    print(f"[3/3] Loading all {total} OCR text files ...")
    texts = []
    missing = []
    for p in range(1, total + 1):
        txt_path = os.path.join(TEXT_DIR, f"page_{p:04d}.txt")
        if os.path.exists(txt_path):
            with open(txt_path, encoding="utf-8") as f:
                texts.append(f.read())
        else:
            texts.append("")
            missing.append(p)
    if missing:
        print(f"      Warning: {len(missing)} pages missing OCR text: {missing[:10]}{'...' if len(missing)>10 else ''}")

    print(f"[3/3] Converting all pages to images for PDF build ...")
    images = convert_from_path(INPUT_PDF, dpi=DPI)

    print(f"[3/3] Building searchable PDF ...")
    build_pdf(images, texts, OUTPUT_PDF)

    print(f"\nDone! Output: {OUTPUT_PDF}")


if __name__ == "__main__":
    main()

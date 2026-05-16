"""
pipeline.py — Hadis OCR Pipeline
=================================
Runs OCR on a scanned Amharic PDF and refreshes cleaned per-page text files.
Searchable PDF generation is optional because it is the most CPU-intensive step.

Usage:
    python3 pipeline.py
    python3 pipeline.py --build-pdf
    python3 pipeline.py --input-pdf "ፍቅር-እስከ-መቃብር-.pdf" --text-dir ocr_text_new

Output:
    ocr_text/        — per-page cleaned text files
    hadis_clean.pdf  — searchable PDF when --build-pdf is passed
"""

import argparse
import os
import fitz           # pymupdf
import io

from clean_text import clean

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


def ocr_page(image) -> str:
    """Run Tesseract OCR on a PIL image, return cleaned text."""
    import pytesseract

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


def already_done(page_num: int, text_dir: str) -> bool:
    """Return True if this 1-based page has already been OCR'd."""
    return os.path.exists(os.path.join(text_dir, f"page_{page_num:04d}.txt"))


def clean_all_text_files(total: int, text_dir: str) -> list[int]:
    """Normalize and clean all OCR text files in place."""
    missing = []
    for page_num in range(1, total + 1):
        txt_path = os.path.join(text_dir, f"page_{page_num:04d}.txt")
        if not os.path.exists(txt_path):
            missing.append(page_num)
            continue

        with open(txt_path, encoding="utf-8") as f:
            original = f.read()

        cleaned = clean(original)
        if cleaned != original:
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(cleaned)

    return missing


def parse_args():
    parser = argparse.ArgumentParser(description="Run OCR and clean text files for the Hadis PDF.")
    parser.add_argument(
        "--input-pdf",
        default=INPUT_PDF,
        help=f"Source PDF to OCR. Defaults to {INPUT_PDF}.",
    )
    parser.add_argument(
        "--text-dir",
        default=TEXT_DIR,
        help=f"Directory for per-page OCR text files. Defaults to {TEXT_DIR}.",
    )
    parser.add_argument(
        "--output-pdf",
        default=OUTPUT_PDF,
        help=f"Path for searchable PDF output when --build-pdf is used. Defaults to {OUTPUT_PDF}.",
    )
    parser.add_argument(
        "--build-pdf",
        action="store_true",
        help="Also build the searchable PDF after OCR and cleaning.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    input_pdf = args.input_pdf
    text_dir = args.text_dir
    output_pdf = args.output_pdf

    os.makedirs(text_dir, exist_ok=True)

    # Determine total pages without loading all images first
    doc = fitz.open(input_pdf)
    total = doc.page_count
    doc.close()
    print(f"      {total} pages in PDF.")

    # Find first page that still needs OCR
    first_todo = next((p for p in range(1, total + 1) if not already_done(p, text_dir)), None)

    if first_todo is None:
        print("      All pages already OCR'd — skipping to PDF build step.")
    else:
        from pdf2image import convert_from_path

        print(f"[2/3] Running Tesseract OCR (lang={LANG}), resuming from page {first_todo} ...")
        print(f"[1/3] Converting pages {first_todo}–{total} to images at {DPI} DPI ...")

        for page_num in range(first_todo, total + 1):
            print(f"      Page {page_num}/{total} ...", end="\r")
            images = convert_from_path(
                input_pdf,
                dpi=DPI,
                first_page=page_num,
                last_page=page_num,
            )
            if not images:
                continue

            img = images[0]
            text = ocr_page(img)
            txt_path = os.path.join(text_dir, f"page_{page_num:04d}.txt")
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(text)
        print(f"\n      OCR complete. Text saved to '{text_dir}/'")

    print(f"[3/3] Cleaning OCR text files ...")
    missing = clean_all_text_files(total, text_dir)
    if missing:
        print(f"      Warning: {len(missing)} pages missing OCR text: {missing[:10]}{'...' if len(missing)>10 else ''}")

    if not args.build_pdf:
        print("\nDone! Cleaned text files are up to date. Skipped PDF generation.")
        return

    # Load all texts from disk for PDF build
    print(f"[4/4] Loading all {total} OCR text files ...")
    texts = []
    for p in range(1, total + 1):
        txt_path = os.path.join(text_dir, f"page_{p:04d}.txt")
        if os.path.exists(txt_path):
            with open(txt_path, encoding="utf-8") as f:
                texts.append(f.read())
        else:
            texts.append("")

    from pdf2image import convert_from_path

    print(f"[4/4] Converting all pages to images for PDF build ...")
    images = convert_from_path(input_pdf, dpi=DPI)

    print(f"[4/4] Building searchable PDF ...")
    build_pdf(images, texts, output_pdf)

    print(f"\nDone! Output: {output_pdf}")


if __name__ == "__main__":
    main()

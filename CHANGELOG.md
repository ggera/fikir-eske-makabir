# Hadis PDF OCR Project — Changelog

**Goal**: Remove Amharic word separators `፡` (U+1361) from `hadis.pdf` by replacing them with spaces,
producing a clean searchable PDF (`hadis_clean.pdf`).

**Original file**: `hadis_original.pdf` (280 pages, image-based / scanned — no embedded text)

---

## Attempt Log

### Attempt 1 — Direct text extraction (FAILED)
- Tool: `pymupdf` (fitz)
- Result: Zero text extracted — confirmed PDF is fully image-based (scanned).
- Conclusion: OCR required.

### Attempt 2a — OCR pipeline, missing `poppler` (FAILED)
- Error: `PDFInfoNotInstalledError` — `pdf2image` requires `poppler` utilities (`pdfinfo`, `pdftoppm`)
- Fix: `brew install poppler` ✓

### Attempt 2b — OCR pipeline with poppler (IN PROGRESS)
- Tools: `tesseract` (amh lang), `pytesseract`, `pdf2image`, `reportlab`, `pillow`
- Status: Tesseract installed and Amharic (`amh`) confirmed available.
- Script: `pipeline.py`
- Plan:
  1. Convert each PDF page to a high-res image (300 DPI)
  2. Run Tesseract OCR with `amh` language
  3. Replace all `፡` (U+1361) with ` ` (space) in recognized text
  4. Rebuild a searchable PDF with the text layer overlaid on original images
- Output: `hadis_clean.pdf`

---

## Environment
- macOS
- Python 3.9
- tesseract 5.x with `tesseract-lang` (amh confirmed)
- pymupdf 1.26.5

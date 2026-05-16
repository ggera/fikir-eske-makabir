# fikir-eske-makabir

OCR, text cleanup, and PDF publishing workflow for ፍቅር እስከ መቃብር.

## Repository Contents

- `ocr_text/`: normalized per-page text files used as the main editable source.
- `original-ፍቅር እስከ መቃብር.pdf`: source scan kept in the repository.
- `normalized-fikir-eske-makabir-text.pdf`: quick-look formatted text PDF kept in the repository root.
- `pipeline.py`: OCR and cleanup pipeline for rebuilding the text corpus and optional searchable PDF.
- `clean_text.py`: OCR normalization logic, including Ethiopic numeral conversion and orthography cleanup.
- `build_text_pdf.py`: formatted text-only PDF generator.
- `.github/workflows/release-text-pdf.yml`: GitHub Actions workflow that rebuilds and republishes the rolling PDF release.

## Main Files

- Input scan: `original-ፍቅር እስከ መቃብር.pdf`
- Editable text corpus: `ocr_text/`
- Quick-look repo PDF: `normalized-fikir-eske-makabir-text.pdf`
- Release PDF asset: `normalized-fikir-eske-makabir-text.pdf`

## Local Usage

Create or activate a Python environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Refresh OCR text from the source PDF:

```bash
python pipeline.py --input-pdf "original-ፍቅር እስከ መቃብር.pdf" --text-dir ocr_text
```

Build the formatted text PDF:

```bash
python build_text_pdf.py --text-dir ocr_text --output-pdf normalized-fikir-eske-makabir-text.pdf
```

Optionally build the searchable PDF overlay from the OCR pipeline:

```bash
python pipeline.py --input-pdf "original-ፍቅር እስከ መቃብር.pdf" --text-dir ocr_text --build-pdf
```

## Release Automation

The GitHub Actions workflow runs on pushes to `main` when the text corpus, PDF builder, font, requirements, or workflow file changes.

Each run:

- rebuilds the normalized text PDF from `ocr_text/`
- deletes older releases
- recreates a single rolling release tagged `latest`

This keeps one current downloadable PDF release while also leaving a quick-look copy in the repository root.
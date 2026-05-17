# ፍቅር እስከ መቃብር — Fikir Eske Mekabir

**ፍቅር እስከ መቃብር** (*Fikir Eske Mekabir*, "Love to the Grave") is a landmark Amharic novel by
**Haddis Alemayehu**, first published in 1968.  It is widely regarded as the greatest novel in the
Amharic literary tradition and won the Haile Selassie I Prize for Amharic Literature in 1969.

The purpose of this project is to make this classic work accessible and readable for today's readers
using modern tools — a clean, searchable, properly formatted PDF that opens in any viewer, on any
device, with no technical setup required.

## Download

📥 **[Download the PDF](https://github.com/ggera/fikir-eske-makabir/releases/latest/download/normalized-fikir-eske-makabir-text.pdf)**

The PDF is rebuilt automatically whenever the text corpus is updated.  You do not need a GitHub
account or any knowledge of git to download it — click the link above.

A human-readable landing page is also available at
**https://ggera.github.io/fikir-eske-makabir/** (enable GitHub Pages → `docs/` folder in the repo
settings to activate it).

## Repository Contents

| Path | Description |
|------|-------------|
| `ocr_text/` | One `.txt` file per print page — the canonical editable text source |
| `original-ፍቅር እስከ መቃብር.pdf` | Original scanned source kept for reference |
| `normalized-fikir-eske-makabir-text.pdf` | Quick-look formatted text PDF at the repo root |
| `build_text_pdf.py` | Renders `ocr_text/` into a two-column landscape PDF |
| `pipeline.py` | OCR pipeline for re-extracting text from the source scan |
| `clean_text.py` | Normalization logic (Ethiopic numeral conversion, orthography cleanup) |
| `docs/index.html` | GitHub Pages landing page for search-engine discoverability |
| `.github/workflows/release-text-pdf.yml` | CI workflow that rebuilds and republishes the rolling PDF release |

## Contributing

Corrections are welcome.  The text is stored one page per file in `ocr_text/` — for example,
`ocr_text/page_0042.txt` contains the text of print page 42.

**Please open one pull request per page.**  This makes it easy to review exactly what changed and
why.

### Step-by-step

1. **Fork** the repository on GitHub and clone your fork locally.
2. **Create a branch** named after the page you are fixing, e.g. `fix/page-0042`.
3. **Edit** only the relevant file(s) in `ocr_text/`.  Common issues to look for:
   - Words broken across print lines (OCR captured the line-break as a space or newline inside
     the word)
   - Merged words (two adjacent words run together without a space)
   - Wrong Ethiopic character (e.g. `ሀ`/`ሃ`/`ሐ`/`ሓ` confusion)
   - Spurious digits or punctuation introduced by the OCR engine
4. **Commit** with a message that names the page and describes the fix, e.g.:
   ```
   ocr: fix line-break splits on page_0042
   
   ሚ↵ኒስትሩ → ሚኒስትሩ  (L8-9, newline split)
   አለ ቀቀው → አለቀቀው   (L14, space split)
   ```
5. **Push** your branch and open a pull request against `main`.  In the PR description note
   the page number and briefly explain each change.

Only files inside `ocr_text/` need to be modified for text corrections.  Changes to
`build_text_pdf.py`, fonts, or the pipeline require a separate discussion first.

## Local Usage

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Build the formatted text PDF from the editable corpus:

```bash
python build_text_pdf.py --text-dir ocr_text --output-pdf normalized-fikir-eske-makabir-text.pdf
```

Re-extract text from the original scan (requires `tesseract` with Amharic support):

```bash
python pipeline.py --input-pdf "original-ፍቅር እስከ መቃብር.pdf" --text-dir ocr_text
```

## Release Automation

A GitHub Actions workflow triggers on every push to `main` that touches `ocr_text/`,
`build_text_pdf.py`, fonts, requirements, or the workflow file itself.  Each run:

- rebuilds the formatted text PDF from `ocr_text/`
- deletes any previous rolling releases
- recreates a single release tagged `latest` with the new PDF attached

This ensures the download link above always points to the most up-to-date version of the text.

## Credits

**OCR normalisation — Hamburg `amseg` library**
Amharic text normalisation (homophone canonicalisation, segmentation support) is performed with the
[`amseg`](https://pypi.org/project/amseg/) package developed at the
[Language Technology group, Universität Hamburg](https://www.ltl.uni-hamburg.de/).

**Ethiopic typeface — Geez Manuscript Zemen**
The PDF is set in *Geez Manuscript Zemen*, a free Ethiopic Unicode font.
Download and further information: **[font.et](http://font.et/)**

**PDF rendering — ReportLab**
Page layout and PDF generation use the open-source
[ReportLab](https://www.reportlab.com/opensource/) toolkit.
"""
clean_text.py — Clean up OCR punctuation noise in ocr_text/*.txt
=================================================================
Removes punctuation characters that add no reading value, replacing
them with a single space.  Converts Ethiopic (Ge'ez) numerals to
Arabic numerals so Gen-Z readers can follow the text easily.

Characters KEPT:
  ።   U+1362  Ethiopic Full Stop
  !   U+0021  Exclamation Mark
  ?   U+003F  Question Mark
  "   U+201C  Left Double Quotation Mark
  "   U+201D  Right Double Quotation Mark
  '   U+0027  Apostrophe
  "   U+0022  Quotation Mark
  «   U+00AB  Left-Pointing Double Angle Quotation Mark
  »   U+00BB  Right-Pointing Double Angle Quotation Mark
  ‹   U+2039  Single Left-Pointing Angle Quotation Mark
  ›   U+203A  Single Right-Pointing Angle Quotation Mark

Characters REMOVED (→ space):
  ፤ ፣ ፥ ፦ ፡  — Ethiopic punctuation
  .  ,  :  ;  -  |  *  #  =  /  +  %
  (  )  [  ]  <  >

Ethiopic digits (U+1369–U+137C) → converted to Arabic numerals.
"""

import os
import re

TEXT_DIR = "ocr_text"

# Characters to replace with a space
REMOVE = set("፤፣፥፦፡.,;:-|*#=/+%()[]<>")

# ── Ethiopic numeral conversion ───────────────────────────────────────────

_ETHIO_VAL = {
    '፩': 1,  '፪': 2,  '፫': 3,  '፬': 4,  '፭': 5,
    '፮': 6,  '፯': 7,  '፰': 8,  '፱': 9,
    '፲': 10, '፳': 20, '፴': 30, '፵': 40, '፶': 50,
    '፷': 60, '፸': 70, '፹': 80, '፺': 90,
    '፻': 100, '፼': 10000,
}

_ETHIO_NUM_RE = re.compile(r'[፩፪፫፬፭፮፯፰፱፲፳፴፵፶፷፸፹፺፻፼]+')
_HEADER_TITLE_RE = re.compile(r"ፍቅር\s+[እአ]ስ\S*\s+[›«»‹›“”'\"]*መ\S*")
_LABIALIZED_REPLACEMENTS = {
    "ሁዋ": "ኋ",
    "ሉዋ": "ሏ",
    "ሙዋ": "ሟ",
    "ሩዋ": "ሯ",
    "ሱዋ": "ሷ",
    "ሹዋ": "ሿ",
    "ቁዋ": "ቋ",
    "ቡዋ": "ቧ",
    "ቱዋ": "ቷ",
    "ቹዋ": "ቿ",
    "ኑዋ": "ኗ",
    "ኙዋ": "ኟ",
    "ኩዋ": "ኳ",
    "ዙዋ": "ዟ",
    "ዱዋ": "ዷ",
    "ጉዋ": "ጓ",
    "ጡዋ": "ጧ",
    "ጩዋ": "ጯ",
    "ጹዋ": "ጿ",
    "ፉዋ": "ፏ",
}
_POSSESSIVE_WA_REPLACEMENTS = {
    "ህዋ": "ኋ",
    "ልዋ": "ሏ",
    "ምዋ": "ሟ",
    "ርዋ": "ሯ",
    "ስዋ": "ሷ",
    "ሽዋ": "ሿ",
    "ቅዋ": "ቋ",
    "ብዋ": "ቧ",
    "ትዋ": "ቷ",
    "ችዋ": "ቿ",
    "ንዋ": "ኗ",
    "ኝዋ": "ኟ",
    "ክዋ": "ኳ",
    "ዝዋ": "ዟ",
    "ድዋ": "ዷ",
    "ግዋ": "ጓ",
    "ጥዋ": "ጧ",
    "ጭዋ": "ጯ",
    "ጽዋ": "ጿ",
    "ፍዋ": "ፏ",
}
_FEMININE_PRONOUN_REPLACEMENTS = {
    "አሷ": "እሷ",
    "ኢሷ": "እሷ",
    "እሰዋ": "እሷ",
}


def _ethio_to_arabic(seq: str) -> str:
    """Convert a run of Ethiopic numeral characters to an Arabic numeral string.

    The Ge'ez system is additive with ፻ (100) and ፼ (10 000) acting as
    multipliers for the group that precedes them:
      ፲፪        → 12
      ፪፻        → 200
      ፪፻፲፪     → 212
      ፻፻        → 10 000  (edge case: treat each ፻ as 100)
    """
    if seq and set(seq) == {'፻'}:
        return str(100 ** len(seq))

    total = 0
    group = 0  # digits accumulated before next multiplier
    for ch in seq:
        v = _ETHIO_VAL[ch]
        if v == 10000:
            group = group or 1
            total += group * 10000
            group = 0
        elif v == 100:
            group = group or 1
            total += group * 100
            group = 0
        else:
            group += v
    total += group
    return str(total)


def _looks_like_running_header(line: str) -> bool:
    """Return True for short OCR header/footer lines containing the book title."""
    stripped = line.strip()
    if not stripped:
        return False

    normalized = re.sub(r"[«»‹›“”'\"!?።]+", " ", stripped)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    tokens = normalized.split()
    title_hits = sum(
        1 for token in tokens
        if token.startswith("ፍቅር") or token.startswith("እስ") or token.startswith("መቃ")
    )

    if normalized.count("ፍቅር") >= 2 and len(tokens) <= 12:
        return True

    # Body mentions of the title tend to be longer sentences. Headers are short.
    if len(tokens) > 8:
        return False

    if title_hits >= 2:
        return True

    if title_hits >= 1 and len(tokens) <= 3:
        return True

    return bool(_HEADER_TITLE_RE.search(normalized))


def _normalize_labialized_forms(text: str) -> str:
    """Convert old-style Xዋ spellings to modern precomposed Ethiopic forms."""
    for original, replacement in _LABIALIZED_REPLACEMENTS.items():
        text = text.replace(original, replacement)

    for original, replacement in _POSSESSIVE_WA_REPLACEMENTS.items():
        text = text.replace(original, replacement)

    for original, replacement in _FEMININE_PRONOUN_REPLACEMENTS.items():
        text = text.replace(original, replacement)

    return text


def clean(text: str) -> str:
    # Convert Ethiopic numerals to Arabic before anything else
    text = _ETHIO_NUM_RE.sub(lambda m: _ethio_to_arabic(m.group()), text)
    text = _normalize_labialized_forms(text)
    # Replace each unwanted character with a space
    chars = [" " if ch in REMOVE else ch for ch in text]
    result = "".join(chars)
    # Collapse only spaces so intentional tab alignment can be preserved.
    result = re.sub(r" {2,}", " ", result)
    # Remove space before Ethiopic punctuation (e.g. "ር ።" → "ར།")
    result = re.sub(r" +([።!?])", r"\1", result)
    # Drop repeated running headers/footers that OCR captured from the source pages.
    result = "\n".join(
        line for line in result.splitlines()
        if not _looks_like_running_header(line)
    )
    result = re.sub(r"\n{3,}", "\n\n", result)
    # Remove trailing whitespace on each line
    result = "\n".join(line.rstrip() for line in result.splitlines())
    return result


def main():
    files = sorted(f for f in os.listdir(TEXT_DIR) if f.endswith(".txt"))
    print(f"Cleaning {len(files)} files in '{TEXT_DIR}/' ...")
    for fname in files:
        path = os.path.join(TEXT_DIR, fname)
        original = open(path, encoding="utf-8").read()
        cleaned = clean(original)
        with open(path, "w", encoding="utf-8") as f:
            f.write(cleaned)
    print("Done.")


if __name__ == "__main__":
    main()

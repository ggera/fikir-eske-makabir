"""
clean_text.py — Clean up OCR punctuation noise in ocr_text/*.txt
=================================================================
Removes punctuation characters that add no reading value, replacing
them with a single space.

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
  Ethiopic digits/numbers (U+1369–U+137C) — kept as numeric content

Characters REMOVED (→ space):
  ፤ ፣ ፥ ፦ ፡  — Ethiopic punctuation
  .  ,  :  ;  -  |  *  #  =  /  +  %
  (  )  [  ]  <  >
"""

import os
import re

TEXT_DIR = "ocr_text"

# Characters to replace with a space
REMOVE = set("፤፣፥፦፡.,;:-|*#=/+%()[]<>")

def clean(text: str) -> str:
    # Replace each unwanted character with a space
    chars = [" " if ch in REMOVE else ch for ch in text]
    result = "".join(chars)
    # Collapse runs of spaces/tabs into a single space (preserve newlines)
    result = re.sub(r"[^\S\n]+", " ", result)
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

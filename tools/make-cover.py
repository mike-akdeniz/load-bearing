#!/usr/bin/env python3
"""Draw the book's cover: docs/cover.png, 1600 x 2560.

    python3 tools/make-cover.py

1600 x 2560 is the size Google Play Books asks for. Plain typography in
upright Charter, the PDF's typeface.
tools/build-book.py puts the result on the EPUB and as the PDF's first page.
Needs Pillow.
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "cover.png"
CHARTER = "/System/Library/Fonts/Supplemental/Charter.ttc"
ROMAN, BOLD = 0, 3

W, H = 1600, 2560
MARGIN = 150
PAPER = "#F3EFE6"  # tools/build-book.py fills the PDF cover page with this too
INK = "#1F1F1F"
SOFT = "#4A4A4A"


def font(face, size):
    return ImageFont.truetype(CHARTER, size, index=face)


def main():
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)

    # The title fills the text block's width.
    size = 230
    while d.textlength("Load-Bearing", font=font(BOLD, size)) > W - 2 * MARGIN:
        size -= 2
    d.text((MARGIN, 700), "Load-Bearing", font=font(BOLD, size), fill=INK, anchor="ls")

    sub = font(ROMAN, 88)
    for i, line in enumerate(["Which Software Principles",
                              "Hold, and Where They Stop"]):
        d.text((MARGIN, 900 + i * 124), line, font=sub, fill=SOFT, anchor="ls")

    d.text((MARGIN, H - 220), "Mike Akdeniz", font=font(ROMAN, 104),
           fill=INK, anchor="ls")

    img.save(OUT, optimize=True)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()

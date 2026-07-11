#!/usr/bin/env python3
"""Crop and upscale a region of a saved RE scan for reading fine print / author signatures.

Usage:
    python3 crop.py <scan.png> <x0> <y0frac> <x1> <y1frac> <out.png> [scale]

x0/x1 are absolute pixel columns; y0frac/y1frac are fractions (0..1) of the image height
(handy because column heights are consistent but you rarely know the exact pixel rows).
scale defaults to 1.8x.

Column layout for a typical 4-column spread (~3620 px wide):
    left page  : col A x 0-880,    col B x 880-1780
    right page : col C x 1840-2720, col D x 2720-3620
"""
import sys
from PIL import Image


def main():
    if len(sys.argv) < 7:
        print(__doc__)
        sys.exit(1)
    fn = sys.argv[1]
    x0, x1 = int(sys.argv[2]), int(sys.argv[4])
    y0f, y1f = float(sys.argv[3]), float(sys.argv[5])
    out = sys.argv[6]
    scale = float(sys.argv[7]) if len(sys.argv) > 7 else 1.8

    im = Image.open(fn)
    w, h = im.size
    crop = im.crop((x0, int(h * y0f), x1, int(h * y1f)))
    crop = crop.resize((int(crop.width * scale), int(crop.height * scale)))
    crop.save(out)
    print(f"saved {out} {crop.size} (from {fn} {im.size})")


if __name__ == "__main__":
    main()

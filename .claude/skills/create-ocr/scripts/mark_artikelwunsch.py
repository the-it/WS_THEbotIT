#!/usr/bin/env python3
"""Append " OCR erstellt" to the Artikelwunsch lines of successfully saved lemmas.

Usage: mark_artikelwunsch.py <batch> [--save]

Takes the SAVED lemmas from <batch>/edit_results.json, fetches the live
Artikelwunsch page, and marks each line that links one of them (matched by
lemma, not line number) and does not already say "OCR erstellt". All marks go
into ONE edit as THEbotIT. Dry run by default: prints the changed lines.
"""
import argparse
import os
import re

import pywikibot
from artikelwunsch_titles import OK_RE, PAGE
from common import load_json

SUMMARY = "OCR für gewünschte Artikel erstellt vermerkt"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("batch")
    ap.add_argument("--save", action="store_true")
    args = ap.parse_args()
    saved = {t for t, v in load_json(os.path.join(args.batch, "edit_results.json")).items()
             if v == "SAVED"}

    site = pywikibot.Site("de", "wikisource")
    page = pywikibot.Page(site, PAGE)
    lines = page.text.split("\n")
    marked = []
    for i, line in enumerate(lines):
        if "OCR erstellt" in line or OK_RE.search(line):
            continue
        links = {m.group(1).strip().replace("_", " ") for m in re.finditer(r"\[\[(RE:[^\]|#]+)", line)}
        hit = sorted(links & saved)
        if hit:
            lines[i] = line.rstrip() + " OCR erstellt"
            marked.extend(hit)
            print(f"  {lines[i]}")
    if not marked:
        print("no Artikelwunsch lines to mark")
        return 0
    print(f"{len(marked)} lemma(s) to mark: {', '.join(marked)}")
    if args.save:
        site.login()
        if site.user() != "THEbotIT":
            raise SystemExit(f"logged in as {site.user()!r}, expected THEbotIT")
        page.text = "\n".join(lines)
        page.save(summary=SUMMARY, minor=False)
        print("saved")
    else:
        print("dry run - pass --save to write")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Harvest open RE lemmas from the Artikelwunsch (requested-articles) page.

Usage: artikelwunsch_titles.py <out_titles.txt>

Keeps every [[RE:...]] link on a line that carries neither the maintainers'
"ok" marker nor "OCR erstellt" from an earlier run. Pass the result to
select_candidates.py --priority so these lemmas are worked first (and get the
extra TODESJAHR guard).
"""
import argparse
import json
import os
import re
import urllib.parse
import urllib.request

from common import USER_AGENT, WIKISOURCE_API

PAGE = "Paulys Realencyclopädie der classischen Altertumswissenschaft/Artikelwunsch"
LINK_RE = re.compile(r"\[\[(RE:[^\]|#]+)")
# maintainers' "handled" marker, e.g. "* [[RE:Hydra 1]] ok." or "… ok. für [[:w:…]]"
OK_RE = re.compile(r"\]\][^\[]*\bok\b", re.IGNORECASE)


def fetch_page(title: str) -> str:
    body = {"action": "query", "prop": "revisions", "rvprop": "content", "rvslots": "main",
            "format": "json", "formatversion": "2", "titles": title}
    req = urllib.request.Request(WIKISOURCE_API, data=urllib.parse.urlencode(body).encode(),
                                 headers={"User-Agent": USER_AGENT})
    d = json.loads(urllib.request.urlopen(req, timeout=60).read())
    return d["query"]["pages"][0]["revisions"][0]["slots"]["main"]["content"]


def open_lemmas(text: str):
    seen = []
    for line in text.splitlines():
        if "OCR erstellt" in line or OK_RE.search(line):
            continue
        for m in LINK_RE.finditer(line):
            lemma = m.group(1).strip().replace("_", " ")
            if lemma not in seen:
                seen.append(lemma)
    return seen


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("out")
    args = ap.parse_args()
    lemmas = open_lemmas(fetch_page(PAGE))
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write("".join(t + "\n" for t in lemmas))
    print(f"{len(lemmas)} open Artikelwunsch lemmas -> {args.out}")
    for t in lemmas:
        print(f"  {t}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

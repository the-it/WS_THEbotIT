#!/usr/bin/env python3
"""Split the batch into fan-out chunks and render one ocr-proofreader prompt per chunk.

Usage: build_chunks.py <batch> [--chunks 10] [--only <titles.txt>]

Reads <batch>/manifest.json, checks every article's local inputs, and writes
  chunks/chunk_NN.json  the articles of each chunk (paths, meta, scan sizes)
  prompts.json          [{description, prompt}] - one Agent call each,
                        subagent_type "ocr-proofreader"
  not_ready.json        articles held back (missing/empty column text, missing or
                        blank placeholder scan) - re-fetch, or use the 4-column spread
Chunks are balanced by column count (largest article first into the lightest
chunk). --only restricts to the given titles, e.g. to re-spawn articles whose
out/ files are missing (idempotent; stay within 10 subagents per batch).
"""
import argparse
import glob
import os
import string
import sys

from common import col_key, load_json, save_json
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
CROP = os.path.normpath(os.path.join(HERE, "..", "..", "re-stammdaten-check", "scripts", "crop.py"))
PYTHON = sys.executable  # run this script with the repo venv python (has Pillow)
MIN_SCAN_BYTES = 5000  # real column PNGs are 100 KB+; a ~1 KB file is eLexikon's blank placeholder

ARTICLE = """Article $i: $title
  skeleton: $skel
  column text(s): $coltexts
  scan PNG(s): $scans
  BAND=$band  SPALTE_START=$start  SPALTE_END=$end
  out: $out
  notes: $notes"""


def article_entry(b, title, m):
    coltexts, scans, problems = [], [], []
    for col in m["cols"]:
        key = col_key(m["band"], col)
        ct = os.path.join(b, "coltext", key + ".txt")
        sc = os.path.join(b, "scans", key + ".png")
        if not os.path.exists(ct) or os.path.getsize(ct) < 20:
            problems.append(f"column text missing/empty: {key}")
        if not os.path.exists(sc) or os.path.getsize(sc) < MIN_SCAN_BYTES:
            problems.append(f"scan missing/blank (<{MIN_SCAN_BYTES} bytes): {key}")
            size = None
        else:
            with Image.open(sc) as im:
                size = list(im.size)
        coltexts.append(ct)
        scans.append({"path": sc, "size": size})
    return {
        "lemma": title, "band": m["band"], "spalte_start": m["spalte_start"],
        "spalte_end": m["spalte_end"], "span": len(m["cols"]),
        "skeleton": os.path.join(b, "skel", m["fname"] + ".wikitext"),
        "column_texts": coltexts, "scans": scans, "seite_lines": m["seite_lines"],
        "out": os.path.join(b, "out", m["fname"] + ".wikitext"),
        "notes": os.path.join(b, "out", m["fname"] + ".notes.json"),
    }, problems


def render(b, chunk, template):
    blocks = []
    for i, a in enumerate(chunk, 1):
        end = a["spalte_end"] if a["spalte_end"] != a["spalte_start"] else "OFF"
        scans = ", ".join(f"{s['path']} ({s['size'][0]}x{s['size'][1]} px)" for s in a["scans"])
        blocks.append(string.Template(ARTICLE).substitute(
            i=i, title=a["lemma"], skel=a["skeleton"], coltexts=", ".join(a["column_texts"]),
            scans=scans, band=a["band"], start=a["spalte_start"], end=end,
            out=a["out"], notes=a["notes"]))
    return template.safe_substitute(batch=b, crop=CROP, python=PYTHON, n=len(chunk),
                                    articles="\n\n".join(blocks))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("batch")
    ap.add_argument("--chunks", type=int, default=10)
    ap.add_argument("--only", help="restrict to these titles (one per line)")
    args = ap.parse_args()
    b = os.path.abspath(args.batch)
    manifest = load_json(os.path.join(b, "manifest.json"))
    if args.only:
        with open(args.only, encoding="utf-8") as fh:
            wanted = {ln.strip() for ln in fh if ln.strip()}
        manifest = {t: m for t, m in manifest.items() if t in wanted}

    ready, not_ready = [], {}
    for title, m in manifest.items():
        entry, problems = article_entry(b, title, m)
        if problems:
            not_ready[title] = problems
        else:
            ready.append(entry)

    n = max(1, min(args.chunks, len(ready)))
    chunks, load = [[] for _ in range(n)], [0] * n
    for a in sorted(ready, key=lambda a: -a["span"]):
        i = load.index(min(load))
        chunks[i].append(a)
        load[i] += a["span"]

    os.makedirs(os.path.join(b, "chunks"), exist_ok=True)
    os.makedirs(os.path.join(b, "out"), exist_ok=True)
    for old in glob.glob(os.path.join(b, "chunks", "chunk_*.json")):
        os.remove(old)
    with open(os.path.join(HERE, "prompt_template.md"), encoding="utf-8") as fh:
        template = string.Template(fh.read())
    prompts = []
    for i, chunk in enumerate(chunks):
        save_json(os.path.join(b, "chunks", f"chunk_{i:02d}.json"), chunk)
        names = ", ".join(a["lemma"].removeprefix("RE:") for a in chunk)
        prompts.append({"description": f"OCR chunk {i:02d}"[:40], "lemmas": names,
                        "prompt": render(b, chunk, template)})
        print(f"chunk_{i:02d}: {len(chunk)} articles, {load[i]} columns")
    save_json(os.path.join(b, "prompts.json"), prompts)
    save_json(os.path.join(b, "not_ready.json"), not_ready)
    print(f"{len(ready)} ready in {n} chunks; {len(not_ready)} not ready")
    for t, p in not_ready.items():
        print(f"  NOT READY {t}: {'; '.join(p)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

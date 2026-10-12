#!/usr/bin/env python3
"""Split the batch into fan-out chunks and render one ocr-proofreader prompt per chunk.

Usage: build_chunks.py <batch> [--chunks 10] [--only <titles.txt>]
                        [--big-cols 3] [--model auto|opus|sonnet]

Reads <batch>/manifest.json, checks every article's local inputs, and writes
  chunks/chunk_NN.json  the articles of each chunk (paths, meta, scan sizes)
  prompts.json          [{description, lemmas, model, prompt}] - one Agent call each,
                        subagent_type "ocr-proofreader", model = the entry's "model"
  not_ready.json        articles held back (missing/empty column text, missing or
                        blank placeholder scan) - re-fetch, or use the 4-column spread
  crops/<HHMMSS>_chunk_NN/  one private crop dir per chunk and run
Model per article (--model auto, the default): articles spanning --big-cols columns or
more go to opus, shorter ones to sonnet (sonnet proofreads short articles about as well
at ~60 % of the cost; see SKILL.md "Fan-out"). A chunk never mixes models. The chunk
budget is split between the two models in proportion to their column load, at least one
chunk each. --model opus|sonnet puts the whole batch on one model.
Chunks are balanced by column count (largest article first into the lightest
chunk). --only restricts to the given titles, e.g. to re-spawn articles whose
out/ files are missing (idempotent; stay within 10 subagents per batch).
"""
import argparse
import glob
import os
import string
import sys
import time

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


def render(b, chunk, template, crops):
    blocks = []
    for i, a in enumerate(chunk, 1):
        end = a["spalte_end"] if a["spalte_end"] != a["spalte_start"] else "OFF"
        scans = ", ".join(f"{s['path']} ({s['size'][0]}x{s['size'][1]} px)" for s in a["scans"])
        blocks.append(string.Template(ARTICLE).substitute(
            i=i, title=a["lemma"], skel=a["skeleton"], coltexts=", ".join(a["column_texts"]),
            scans=scans, band=a["band"], start=a["spalte_start"], end=end,
            out=a["out"], notes=a["notes"]))
    return template.safe_substitute(batch=b, crop=CROP, python=PYTHON, n=len(chunk),
                                    crops=crops, articles="\n\n".join(blocks))


def model_for(article, big_cols, forced):
    if forced != "auto":
        return forced
    return "opus" if article["span"] >= big_cols else "sonnet"


def chunk_budget(loads, counts, total):
    """Split `total` chunks across groups by column load: >= 1 each, <= the group's size."""
    groups = [g for g in loads if counts[g]]
    total = max(total, len(groups))
    budget = {g: 1 for g in groups}
    for _ in range(total - len(groups)):
        open_ = [g for g in groups if budget[g] < counts[g]]
        if not open_:
            break
        # give the next chunk to the group with the most columns per chunk
        g = max(open_, key=lambda x: loads[x] / budget[x])
        budget[g] += 1
    return budget


def balance(articles, n):
    """Largest article first into the lightest chunk. Returns (chunks, loads)."""
    chunks, load = [[] for _ in range(n)], [0] * n
    for a in sorted(articles, key=lambda a: -a["span"]):
        i = load.index(min(load))
        chunks[i].append(a)
        load[i] += a["span"]
    return chunks, load


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("batch")
    ap.add_argument("--chunks", type=int, default=10)
    ap.add_argument("--only", help="restrict to these titles (one per line)")
    ap.add_argument("--big-cols", type=int, default=3,
                    help="articles with at least this many columns go to opus (default 3)")
    ap.add_argument("--model", choices=("auto", "opus", "sonnet"), default="auto",
                    help="auto = per article by --big-cols; opus/sonnet = whole batch")
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

    groups = {}
    for a in ready:
        groups.setdefault(model_for(a, args.big_cols, args.model), []).append(a)
    budget = chunk_budget({g: sum(a["span"] for a in arts) for g, arts in groups.items()},
                          {g: len(arts) for g, arts in groups.items()},
                          min(args.chunks, len(ready)))
    chunks, load, models = [], [], []
    for g in ("opus", "sonnet"):
        if g not in groups:
            continue
        c, ld = balance(groups[g], budget[g])
        chunks += c
        load += ld
        models += [g] * len(c)
    n = len(chunks)

    os.makedirs(os.path.join(b, "chunks"), exist_ok=True)
    os.makedirs(os.path.join(b, "out"), exist_ok=True)
    for old in glob.glob(os.path.join(b, "chunks", "chunk_*.json")):
        os.remove(old)
    with open(os.path.join(HERE, "prompt_template.md"), encoding="utf-8") as fh:
        template = string.Template(fh.read())
    # One crop dir per chunk and run: parallel subagents (and re-spawns next to a
    # still-running chunk) must never overwrite or read each other's crops.
    run = time.strftime("%H%M%S")
    prompts = []
    for i, chunk in enumerate(chunks):
        save_json(os.path.join(b, "chunks", f"chunk_{i:02d}.json"), chunk)
        crops = os.path.join(b, "crops", f"{run}_chunk_{i:02d}")
        os.makedirs(crops, exist_ok=True)
        names = ", ".join(a["lemma"].removeprefix("RE:") for a in chunk)
        prompts.append({"description": f"OCR chunk {i:02d} ({models[i]})"[:40], "lemmas": names,
                        "model": models[i], "prompt": render(b, chunk, template, crops)})
        print(f"chunk_{i:02d}: {models[i]:6s} {len(chunk)} articles, {load[i]} columns")
    save_json(os.path.join(b, "prompts.json"), prompts)
    save_json(os.path.join(b, "not_ready.json"), not_ready)
    print(f"{len(ready)} ready in {n} chunks; {len(not_ready)} not ready")
    for t, p in not_ready.items():
        print(f"  NOT READY {t}: {'; '.join(p)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

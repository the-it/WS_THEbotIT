#!/usr/bin/env python3
"""Snapshot skeletons and list the columns to fetch for the selected articles.

Usage: build_manifest.py <batch>

Reads <batch>/selected.json + all_wikitext.json and writes:
  skel_ref/<f>.wikitext  clean skeleton snapshot - the reference for run_checks.py
                         and apply_edits.py; never give this path to subagents
  skel/<f>.wikitext      working copy handed to subagents (they may edit it)
  manifest.json          {title: {fname, band, spalte_start, spalte_end, cols, seite_lines}}
  columns.json           sorted unique [[band, col], ...] for gen_fetch_js.py
"""
import argparse
import os

from common import SEITE_RE, fname, load_json, save_json, target_info


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("batch")
    args = ap.parse_args()
    b = args.batch
    texts = load_json(os.path.join(b, "all_wikitext.json"))
    selected = load_json(os.path.join(b, "selected.json"))
    for sub in ("skel_ref", "skel"):
        os.makedirs(os.path.join(b, sub), exist_ok=True)

    manifest, columns = {}, set()
    for c in selected:
        title, text = c["title"], texts[c["title"]]
        f = fname(title)
        for sub in ("skel_ref", "skel"):
            with open(os.path.join(b, sub, f + ".wikitext"), "w", encoding="utf-8") as fh:
                fh.write(text)
        info = target_info(text)
        cols = list(range(c["spalte_start"], c["spalte_end"] + 1))
        manifest[title] = {
            "fname": f, "band": c["band"], "spalte_start": c["spalte_start"],
            "spalte_end": c["spalte_end"], "cols": cols,
            "seite_lines": [ln.strip() for ln in info["body"] if SEITE_RE.fullmatch(ln.strip())],
        }
        columns.update((c["band"], col) for col in cols)

    save_json(os.path.join(b, "manifest.json"), manifest)
    save_json(os.path.join(b, "columns.json"), sorted(columns))
    bands = sorted({band for band, _ in columns})
    print(f"articles {len(manifest)}; unique columns {len(columns)}; bands {bands}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

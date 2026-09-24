#!/usr/bin/env python3
"""Move inline {{Seite|…}} tags onto their own line in subagent output (in place).

Usage: fix_seite_ownline.py <batch> [--dry-run]

Subagents often leave a column-break tag inside the running line
("… Strab. {{Seite|753||{{REIA|VII A,1|753}}}} XVII …"); check_assembly.py then
FAILs "Seite line exactly once". This splits such lines at each tag, eating one
adjacent space per side, and leaves the tag's position in the text unchanged.
Run it on <batch>/out/*.wikitext before run_checks.py.
"""
import argparse
import glob
import os

from common import SEITE_RE


def fix(text: str):
    out, moved = [], []
    for line in text.split("\n"):
        stripped = line.strip()
        if not SEITE_RE.search(line) or SEITE_RE.fullmatch(stripped):
            out.append(line)
            continue
        pos = 0
        for m in SEITE_RE.finditer(line):
            before = line[pos:m.start()].removesuffix(" ")
            if before:
                out.append(before)
            out.append(m.group(0))
            moved.append(m.group(0))
            pos = m.end() + (1 if line[m.end():m.end() + 1] == " " else 0)
        if line[pos:]:
            out.append(line[pos:])
    return "\n".join(out), moved


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("batch")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    changed = 0
    for path in sorted(glob.glob(os.path.join(args.batch, "out", "*.wikitext"))):
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        new, moved = fix(text)
        if not moved:
            continue
        changed += 1
        print(f"{os.path.basename(path)}: {', '.join(moved)}")
        if not args.dry_run:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(new)
    print(f"{changed} file(s) {'would change' if args.dry_run else 'fixed'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

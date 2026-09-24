#!/usr/bin/env python3
"""Assemble one long article from body parts proofread by several subagents.

Usage: stitch_parts.py <skeleton.wikitext> <out.wikitext> <part1.wikitext> [<part2> ...]

For articles too long for one subagent (e.g. RE:Gemmen, 64 columns), give each
subagent a contiguous column range and let it write only its BODY part: the
proofread text for its columns, including the {{Seite}} lines that fall inside
its range. Part 1 starts with the bold headword. Parts are joined with a single
newline, so a paragraph break at a part boundary must be inside a part as a
blank line. This script flips KORREKTURSTAND, replaces the target block's
headword/[...]/{{Seite}} body with the joined parts, and keeps {{REAutor}},
categories and sibling blocks byte-identical. Run check_assembly.py afterwards.
"""
import argparse

from common import target_info


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("skeleton")
    ap.add_argument("out")
    ap.add_argument("parts", nargs="+")
    args = ap.parse_args()
    with open(args.skeleton, encoding="utf-8") as fh:
        skel = fh.read()
    info = target_info(skel)
    lines = info["lines"]
    block_end, body_end = info["body_start"], info["autor_line"]
    head = [ln.replace("|KORREKTURSTAND=unvollständig", "|KORREKTURSTAND=unkorrigiert")
            for ln in lines[:block_end]]
    lead_in = [ln for ln in info["body"] if ln.lstrip().startswith(":") and "zum Art." in ln]
    parts = []
    for p in args.parts:
        with open(p, encoding="utf-8") as fh:
            parts.append(fh.read().strip("\n"))
    new = head + lead_in + ["\n".join(parts)] + lines[body_end:]
    text = "\n".join(new) + ("\n" if skel.endswith("\n") else "")
    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write(text)
    print(f"wrote {args.out}: {len(parts)} parts, {len(text)} chars")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

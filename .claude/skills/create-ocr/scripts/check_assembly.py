#!/usr/bin/env python3
"""Structural check of an assembled create-ocr article against its skeleton.

Usage: check_assembly.py <skeleton.wikitext> <new.wikitext>

Verifies the invariants of the create-ocr skill mechanically:
  - the {{REDaten}} block is byte-identical except exactly the
    KORREKTURSTAND unvollständig -> unkorrigiert flip
  - every skeleton {{Seite|...}} line survives byte-identically, exactly once,
    in the same order, and no extra {{Seite templates appear
  - the {{REAutor|...}} sequence and all [[Kategorie:...]] lines are unchanged
  - no leftovers: "[...]" placeholder, U+FEFF/zero-width chars, "== RE:" or a
    bare "RE:<lemma>" heading line
  - the body directly follows the REDaten block with the bold '''headword'''
  - body length is plausible for the column span (WARN only)

Exit code 0 = no FAIL (warnings allowed), 1 = at least one FAIL.
"""
import re
import sys

failures = []
warnings = []


def check(ok: bool, label: str, detail: str = "") -> None:
    if ok:
        print(f"OK    {label}")
    else:
        failures.append(label)
        print(f"FAIL  {label}{': ' + detail if detail else ''}")


def warn(cond: bool, label: str, detail: str = "") -> None:
    if cond:
        warnings.append(label)
        print(f"WARN  {label}{': ' + detail if detail else ''}")


def redaten_block(lines):
    """Return (start, end) line indexes of the {{REDaten ... }} block."""
    try:
        start = next(i for i, l in enumerate(lines) if l.strip() == "{{REDaten")
        end = next(i for i in range(start + 1, len(lines)) if lines[i].strip() == "}}")
    except StopIteration:
        return None
    return start, end


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    with open(sys.argv[1], encoding="utf-8") as fh:
        skel = fh.read()
    with open(sys.argv[2], encoding="utf-8") as fh:
        new = fh.read()
    skel_lines, new_lines = skel.splitlines(), new.splitlines()

    # --- REDaten block ---
    sblk, nblk = redaten_block(skel_lines), redaten_block(new_lines)
    check(sblk is not None, "skeleton has one {{REDaten}} block")
    check(nblk is not None, "new text has a {{REDaten}} block")
    verweis_on = False
    span = 1
    if sblk and nblk:
        sfields = skel_lines[sblk[0] : sblk[1] + 1]
        nfields = new_lines[nblk[0] : nblk[1] + 1]
        check(len(sfields) == len(nfields), "REDaten blocks have equal length",
              f"{len(sfields)} vs {len(nfields)} lines")
        for s, n in zip(sfields, nfields):
            if s.startswith("|KORREKTURSTAND="):
                check(s == "|KORREKTURSTAND=unvollständig",
                      "skeleton KORREKTURSTAND is unvollständig", s)
                check(n == "|KORREKTURSTAND=unkorrigiert",
                      "new KORREKTURSTAND is unkorrigiert", n)
            else:
                check(s == n, f"REDaten line unchanged: {s.split('=')[0].lstrip('|') or s}",
                      f"{s!r} -> {n!r}")
        verweis_on = "|VERWEIS=ON" in sfields
        m_start = next((l for l in sfields if l.startswith("|SPALTE_START=")), "")
        m_end = next((l for l in sfields if l.startswith("|SPALTE_END=")), "")
        try:
            start_col = int(m_start.split("=", 1)[1])
            span = 1 if m_end.strip() == "|SPALTE_END=OFF" else (
                int(m_end.split("=", 1)[1]) - start_col + 1)
        except ValueError:
            span = 1

    # --- {{Seite}} lines ---
    skel_seite = [l for l in skel_lines if l.lstrip().startswith("{{Seite|")]
    positions = []
    for line in skel_seite:
        cnt = sum(1 for l in new_lines if l == line)
        check(cnt == 1, f"Seite line exactly once: {line}", f"found {cnt}×")
        if cnt == 1:
            positions.append(new_lines.index(line))
    check(positions == sorted(positions), "Seite lines keep skeleton order")
    n_seite_new = new.count("{{Seite|")
    check(n_seite_new == len(skel_seite),
          "no extra {{Seite templates",
          f"{n_seite_new} in new vs {len(skel_seite)} in skeleton")

    # --- REAutor + categories ---
    skel_aut = re.findall(r"\{\{REAutor\|[^}]*\}\}", skel)
    new_aut = re.findall(r"\{\{REAutor\|[^}]*\}\}", new)
    check(skel_aut == new_aut, "REAutor sequence unchanged",
          f"{skel_aut} -> {new_aut}")
    skel_cat = [l for l in skel_lines if l.startswith("[[Kategorie:")]
    new_cat = [l for l in new_lines if l.startswith("[[Kategorie:")]
    check(skel_cat == new_cat, "Kategorie lines unchanged",
          f"{skel_cat} -> {new_cat}")

    # --- leftovers ---
    check("[...]" not in new, "placeholder [...] gone")
    for ch, name in (("﻿", "U+FEFF BOM"), ("​", "zero-width space"),
                     ("‎", "LTR mark")):
        check(ch not in new, f"no {name}")
    check("== RE:" not in new, "no == RE: == heading left")
    if nblk:
        body_first = next((l for l in new_lines[nblk[1] + 1 :] if l.strip()), "")
        check(body_first.startswith("'''"),
              "body starts with bold headword right after REDaten", body_first[:60])
        check(not re.match(r"^RE:\S", body_first),
              "no bare RE:<lemma> heading line", body_first[:60])

    # --- body length sanity (truncation catch; interior columns are full) ---
    if nblk and not verweis_on and span >= 2:
        body = "\n".join(
            l for l in new_lines[nblk[1] + 1 :]
            if not l.lstrip().startswith("{{Seite|")
            and not l.startswith("[[Kategorie:")
            and "{{REAutor|" not in l)
        warn(len(body) < 1500 * (span - 1),
             "body looks short for its column span",
             f"{len(body)} chars for {span} columns")

    print(f"\nresult: {'FAIL' if failures else 'PASS'} "
          f"({len(failures)} failures, {len(warnings)} warnings)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())

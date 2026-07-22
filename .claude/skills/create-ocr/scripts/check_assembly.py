#!/usr/bin/env python3
"""Structural check of an assembled create-ocr article against its skeleton.

Usage: check_assembly.py <skeleton.wikitext> <new.wikitext>

Verifies the invariants of the create-ocr skill mechanically:
  - the target {{REDaten}} block (the one flipped from KORREKTURSTAND
    unvollständig -> unkorrigiert) is byte-identical except exactly that flip.
    On multi-block Nachtrag pages the target is located by the flip, not by
    position; sibling blocks stay byte-identical (their {{REAutor}} and
    categories are covered by the page-wide checks below).
  - every skeleton {{Seite|...}} line survives byte-identically, exactly once,
    in the same order, and no extra {{Seite templates appear. If the skeleton
    had NO {{Seite}} lines (older stubs), the generated ones are instead checked
    to be well-formed, strictly ascending, and to match the column span.
  - the {{REAutor|...}} sequence and all [[Kategorie:...]] lines are unchanged
  - no leftovers: "[...]" placeholder, U+FEFF/zero-width chars, "== RE:" or a
    bare "RE:<lemma>" heading line
  - the body starts with the bold '''headword''' (a Nachtrag ": S. ... zum Art."
    lead-in line may precede it)
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


def redaten_blocks(lines):
    """Yield (start, end) line indexes for every {{REDaten ... }} block."""
    i, n = 0, len(lines)
    while i < n:
        if lines[i].strip() == "{{REDaten":
            try:
                end = next(j for j in range(i + 1, n) if lines[j].strip() == "}}")
            except StopIteration:
                return
            yield (i, end)
            i = end + 1
        else:
            i += 1


def target_block(lines, wanted_status):
    """Return (start, end) of the block whose KORREKTURSTAND == wanted_status.

    Locating by the flip (not by position) is what lets a Nachtrag / multi-band
    page with several stacked {{REDaten}} chains be filled: only the single
    unvollständig block is the target; the rest are left untouched.
    """
    for start, end in redaten_blocks(lines):
        if f"|KORREKTURSTAND={wanted_status}" in (l.strip() for l in lines[start:end + 1]):
            return start, end
    return None


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    with open(sys.argv[1], encoding="utf-8") as fh:
        skel = fh.read()
    with open(sys.argv[2], encoding="utf-8") as fh:
        new = fh.read()
    skel_lines, new_lines = skel.splitlines(), new.splitlines()

    # --- target {{REDaten}} block (located by the KORREKTURSTAND flip) ---
    sblk = target_block(skel_lines, "unvollständig")
    nblk = target_block(new_lines, "unkorrigiert")
    check(sblk is not None, "skeleton has an unvollständig {{REDaten}} block")
    check(nblk is not None, "new text has an unkorrigiert {{REDaten}} block")
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
    new_seite = [l for l in new_lines if l.lstrip().startswith("{{Seite|")]
    if skel_seite:
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
    else:
        # Older stubs (esp. Nachträge) carry no pre-generated {{Seite}} lines; the
        # assembly step generates them from eLexikon's column breaks -> validate those.
        cols = []
        for line in new_seite:
            m = re.match(r"\{\{Seite\|(\d+)", line.strip())
            cols.append(int(m.group(1)) if m else None)
        check(all(c is not None for c in cols),
              "generated {{Seite}} lines are well-formed", str(new_seite[:3]))
        check(cols == sorted(cols) and len(set(cols)) == len(cols),
              "generated {{Seite}} lines strictly ascending", str(cols))
        if span >= 2:
            check(len(new_seite) == span - 1,
                  "generated {{Seite}} count matches column span",
                  f"{len(new_seite)} lines for span {span}")

    # --- REAutor + categories (cover every block on the page) ---
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
        after = [l for l in new_lines[nblk[1] + 1 :] if l.strip()]
        # a Nachtrag lead-in (": S. 299, 48 zum Art. ...") may precede the headword
        body_first = next((l for l in after if not l.lstrip().startswith(":")), "")
        check(body_first.startswith("'''"),
              "body starts with bold headword right after REDaten", body_first[:60])
        check(not re.match(r"^RE:\S", body_first),
              "no bare RE:<lemma> heading line", body_first[:60])

    # --- body length sanity (truncation catch; interior columns are full) ---
    if nblk and not verweis_on and span >= 2:
        # scope the body to the target block only (up to its own {{REAutor}}),
        # so sibling blocks on a multi-block page don't mask a truncated body
        end_idx = next((i for i in range(nblk[1] + 1, len(new_lines))
                        if "{{REAutor|" in new_lines[i]), len(new_lines))
        body = "\n".join(
            l for l in new_lines[nblk[1] + 1 : end_idx]
            if not l.lstrip().startswith("{{Seite|"))
        warn(len(body) < 1500 * (span - 1),
             "body looks short for its column span",
             f"{len(body)} chars for {span} columns")

    print(f"\nresult: {'FAIL' if failures else 'PASS'} "
          f"({len(failures)} failures, {len(warnings)} warnings)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())

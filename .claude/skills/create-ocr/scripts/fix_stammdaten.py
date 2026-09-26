#!/usr/bin/env python3
"""Fix scan-verified Stammdaten errors found during an OCR batch (pywikibot as THEbotIT).

Usage: fix_stammdaten.py <batch> --collect
       fix_stammdaten.py <batch> [--save] [--only <lemma> ...]

--collect drafts <batch>/stammdaten_fixes.json from every out/<f>.notes.json that
carries a "stammdaten_fix" entry (merged into an existing file; entries already
there win). Review every entry against the scan before running the fix pass - the
subagents are offline and sometimes swap old and new values.

stammdaten_fixes.json: {lemma: {"fields": {FIELD: {"old": ..., "new": ...}},
                                "evidence": "col 2235: [Bürchner.] ends ..."}}
FIELD is SPALTE_START, SPALTE_END, VORGÄNGER, NACHFOLGER or REAUTOR (the
{{REAutor|…}} value). Neighbour pages outside the batch may be listed too (for the
reciprocal V/N fix); on those only VORGÄNGER/NACHFOLGER/REAUTOR are changed and
the page must hold exactly one {{REDaten}} block. Lemma moves (Greek headword,
letter case, macrons) are out of scope - use re-stammdaten-check for those.

Fix pass (DRY RUN by default, --save to write): per lemma
  - guard: batch lemmas' live text still equals skel_ref/; every field's live
    value equals "old" (else SKIP - catches swapped old/new values);
  - line-replace the fields in the target block (the unvollständig block for
    batch lemmas); if SPALTE_* changed and the skeleton carried pre-generated
    {{Seite}} lines, regenerate them for the new span in skeleton style;
  - one edit, summary "Stammdaten am Scan korrigiert: SPALTE_END 2236 → OFF";
  - batch lemmas: write the new text to skel_ref/ and skel/, update manifest.json
    (spalte_*, cols, seite_lines) and columns.json. Afterwards run gen_fetch_js.py
    for any new columns and run_checks.py as usual.
Writes <batch>/stammdaten_results.json {lemma: status}. Run with the repo venv python.
"""
import argparse
import os
import re

from common import SEITE_RE, field, load_json, save_json, target_info
from check_assembly import redaten_blocks

FIELDS = ("SPALTE_START", "SPALTE_END", "VORGÄNGER", "NACHFOLGER", "REAUTOR")
REAUTOR_RE = re.compile(r"\{\{REAutor\|([^{}]*)\}\}")


def collect(b: str) -> int:
    manifest = load_json(os.path.join(b, "manifest.json"))
    path = os.path.join(b, "stammdaten_fixes.json")
    fixes = load_json(path, default={})
    added = 0
    for title, m in manifest.items():
        notes = load_json(os.path.join(b, "out", m["fname"] + ".notes.json"), default={})
        fix = notes.get("stammdaten_fix")
        if not fix:
            continue
        for lemma, entry in ({title: fix} | fix.get("neighbours", {})).items():
            if lemma in fixes:
                continue
            fixes[lemma] = {"fields": entry.get("fields", {}),
                            "evidence": entry.get("evidence", fix.get("evidence", ""))}
            added += 1
    save_json(path, fixes)
    print(f"{added} fix(es) drafted -> {path}; review each against the scan before the fix pass")
    for lemma, entry in fixes.items():
        changes = ", ".join(f"{k} {v.get('old')!r} -> {v.get('new')!r}" for k, v in entry["fields"].items())
        print(f"  {lemma}: {changes}")
    return 0


def seite_line(band: str, col: int) -> str:
    return f"{{{{Seite|{col}}}}}" if col % 2 == 0 else f"{{{{Seite|{col}||{{{{REIA|{band}|{col}}}}}}}}}"


def apply_fix(text: str, fields: dict, in_batch: bool):
    """Return (new_text, error). Only the target block and its REAutor line change."""
    lines = text.splitlines()
    if in_batch:
        info = target_info(text)
        start, body_start, autor = info["block_start"], info["body_start"], info["autor_line"]
    else:
        blocks = list(redaten_blocks(lines))
        if len(blocks) != 1:
            return None, f"{len(blocks)} REDaten blocks on neighbour page (need exactly 1)"
        start, body_start = blocks[0][0], blocks[0][1] + 1
        autor = next((i for i in range(body_start, len(lines)) if "{{REAutor|" in lines[i]), None)
        if any(f.startswith("SPALTE_") for f in fields):
            return None, "SPALTE_* fixes only on batch skeletons"
    block_end = body_start - 1
    for name, change in fields.items():
        if name not in FIELDS:
            return None, f"unsupported field {name}"
        old, new = str(change["old"]).strip(), str(change["new"]).strip()
        if old == new:
            return None, f"{name}: old == new"
        if name == "REAUTOR":
            if autor is None:
                return None, "no {{REAutor}} line"
            m = REAUTOR_RE.search(lines[autor])
            if not m or m.group(1).strip() != old:
                return None, f"REAUTOR live {m.group(1) if m else None!r} != old {old!r}"
            lines[autor] = lines[autor].replace(m.group(0), f"{{{{REAutor|{new}}}}}", 1)
            continue
        idx = next((i for i in range(start, block_end) if lines[i].startswith(f"|{name}=")), None)
        if idx is None:
            return None, f"no |{name}= line"
        live = lines[idx][len(name) + 2:].strip()
        if live != old:
            return None, f"{name} live {live!r} != old {old!r}"
        lines[idx] = f"|{name}={new}"

    if in_batch and any(f.startswith("SPALTE_") for f in fields):
        block = lines[start:block_end + 1]
        body = lines[body_start:autor]
        old_seite = [i for i, ln in enumerate(body) if SEITE_RE.fullmatch(ln.strip())]
        if old_seite:
            band = field(block, "BAND")
            s = int(field(block, "SPALTE_START"))
            e_raw = field(block, "SPALTE_END")
            e = s if e_raw in ("", "OFF") else int(e_raw)
            if e < s:
                return None, f"new span invalid ({s}..{e})"
            keep = [ln for i, ln in enumerate(body) if i not in old_seite]
            new_body = keep + [seite_line(band, c) for c in range(s + 1, e + 1)]
            lines[body_start:autor] = new_body
    new_text = "\n".join(lines) + ("\n" if text.endswith("\n") else "")
    return new_text, ""


def summary_for(fields: dict) -> str:
    parts = []
    for name, change in fields.items():
        label = "REAutor" if name == "REAUTOR" else name
        parts.append(f"{label} {change['old']} → {change['new']}")
    return "Stammdaten am Scan korrigiert: " + ", ".join(parts)


def refresh_manifest(b: str, title: str, text: str, manifest: dict) -> None:
    info = target_info(text)
    s = int(info["spalte_start"])
    e_raw = info["spalte_end"] or "OFF"
    e = s if e_raw == "OFF" else int(e_raw)
    m = manifest[title]
    m.update(spalte_start=s, spalte_end=e, cols=list(range(s, e + 1)),
             seite_lines=[ln.strip() for ln in info["body"] if SEITE_RE.fullmatch(ln.strip())])
    cpath = os.path.join(b, "columns.json")
    cols = {tuple(c) for c in load_json(cpath, default=[])}
    cols.update((m["band"], c) for c in m["cols"])
    save_json(cpath, sorted(cols))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("batch")
    ap.add_argument("--collect", action="store_true", help="draft stammdaten_fixes.json from notes")
    ap.add_argument("--save", action="store_true", help="really save (default: dry run)")
    ap.add_argument("--only", nargs="*", help="restrict to these lemmas")
    args = ap.parse_args()
    b = args.batch
    if args.collect:
        return collect(b)

    import pywikibot  # only needed for the fix pass

    manifest = load_json(os.path.join(b, "manifest.json"))
    fixes = load_json(os.path.join(b, "stammdaten_fixes.json"))
    site = pywikibot.Site("de", "wikisource")
    if args.save:
        site.login()
        if site.user() != "THEbotIT":
            raise SystemExit(f"logged in as {site.user()!r}, expected THEbotIT")

    results_path = os.path.join(b, "stammdaten_results.json")
    results = load_json(results_path, default={}) if args.save else {}
    for title, entry in fixes.items():
        if args.only and title not in args.only:
            continue
        if args.save and results.get(title) == "SAVED":
            continue
        in_batch = title in manifest
        page = pywikibot.Page(site, title)
        if not page.exists():
            results[title] = "SKIP: page missing"
            continue
        live = page.text
        if in_batch:
            with open(os.path.join(b, "skel_ref", manifest[title]["fname"] + ".wikitext"), encoding="utf-8") as fh:
                if live.rstrip("\n") != fh.read().rstrip("\n"):
                    results[title] = "SKIP: live page changed since fetch"
                    continue
        new_text, err = apply_fix(live, entry["fields"], in_batch)
        if err:
            results[title] = f"SKIP: {err}"
            continue
        summary = summary_for(entry["fields"])
        if not args.save:
            results[title] = f"WOULD_SAVE: {summary}"
            continue
        page.text = new_text
        try:
            page.save(summary=summary, minor=False)
        except Exception as exc:  # noqa: BLE001 - record and continue with the next page
            results[title] = f"ERROR: {exc}"
            save_json(results_path, results)
            continue
        results[title] = "SAVED"
        if in_batch:
            fresh = pywikibot.Page(site, title).get(force=True)
            for sub in ("skel_ref", "skel"):
                with open(os.path.join(b, sub, manifest[title]["fname"] + ".wikitext"), "w", encoding="utf-8") as fh:
                    fh.write(fresh)
            refresh_manifest(b, title, fresh, manifest)
            save_json(os.path.join(b, "manifest.json"), manifest)
        save_json(results_path, results)

    if args.save:
        save_json(results_path, results)
    for t, v in results.items():
        print(f"  {t}: {v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Apply the per-article guards and pick the batch (priority lemmas first, then shortest).

Usage: select_candidates.py <batch> --n N [--priority <titles.txt>] [--exclude <titles.txt>]

Reads <batch>/all_wikitext.json (fetch_wikitext.py output; fetch the priority
titles into the same file). Guards, each a skip with reason:
  - page missing, excluded, or not exactly one KORREKTURSTAND=unvollständig block
  - NACHTRAG not OFF on the target block
  - target body not pristine (headword / Nachtrag lead-in / [...] / {{Seite}} only)
  - SPALTE_START/SPALTE_END unparsable or span < 1
  - a [[Kategorie:Wikisource:Gemeinfreiheit…]] in the text (cheap pre-check only;
    legal_guard.py does the authoritative API check afterwards)
  - priority (Artikelwunsch) lemmas only: TODESJAHR must be empty/OFF
Writes <batch>/selected.json [{title, band, spalte_start, spalte_end, span, priority}]
and appends skips to <batch>/skipped.json.
"""
import argparse
import os

from common import add_skips, body_is_pristine, load_json, save_json, span_of, target_info


def read_titles(path):
    if not path:
        return []
    with open(path, encoding="utf-8") as fh:
        return [ln.strip().replace("_", " ") for ln in fh if ln.strip()]


def check(title, text, priority):
    if text is None:
        return None, "page missing"
    if "[[Kategorie:Wikisource:Gemeinfreiheit" in text:
        return None, "Wikisource:Gemeinfreiheit category (legal guard)"
    try:
        info = target_info(text)
    except ValueError as exc:
        return None, str(exc)
    if info["nachtrag"] not in (None, "", "OFF"):
        return None, f"NACHTRAG={info['nachtrag']} on target block"
    reason = body_is_pristine(info["body"])
    if reason:
        return None, reason
    try:
        span = span_of(info["spalte_start"], info["spalte_end"])
    except (TypeError, ValueError):
        return None, f"bad SPALTE start={info['spalte_start']!r} end={info['spalte_end']!r}"
    if span < 1:
        return None, f"bad span {span}"
    if priority and info["todesjahr"] not in (None, "", "OFF"):
        return None, f"TODESJAHR={info['todesjahr']} set (copyright watch)"
    end = int(info["spalte_start"]) + span - 1
    return {"title": title, "band": info["band"], "spalte_start": int(info["spalte_start"]),
            "spalte_end": end, "span": span, "priority": priority}, ""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("batch")
    ap.add_argument("--n", type=int, required=True, help="batch size")
    ap.add_argument("--priority", help="titles worked first (Artikelwunsch)")
    ap.add_argument("--exclude", help="titles never selected (known skips)")
    args = ap.parse_args()

    texts = load_json(os.path.join(args.batch, "all_wikitext.json"))
    priority = read_titles(args.priority)
    exclude = set(read_titles(args.exclude))
    order = priority + [t for t in texts if t not in set(priority)]

    prio_ok, rest_ok, skips = [], [], []
    for title in order:
        if title in exclude:
            skips.append((title, "excluded"))
            continue
        cand, reason = check(title, texts.get(title), title in priority)
        if cand is None:
            skips.append((title, reason))
        elif cand["priority"]:
            prio_ok.append(cand)
        else:
            rest_ok.append(cand)

    rest_ok.sort(key=lambda c: (c["span"], c["title"]))
    selected = (prio_ok + rest_ok)[:args.n]
    save_json(os.path.join(args.batch, "selected.json"), selected)
    add_skips(args.batch, "select", skips)

    hist = {}
    for c in selected:
        hist[c["span"]] = hist.get(c["span"], 0) + 1
    print(f"passing guards: {len(prio_ok)} priority + {len(rest_ok)} worklist; skipped {len(skips)}")
    print(f"selected {len(selected)}; span histogram {dict(sorted(hist.items()))}; "
          f"columns {sum(c['span'] for c in selected)}")
    for t, r in skips:
        if t in priority:
            print(f"  priority skip: {t}: {r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Aggregate the subagents' findings_*.json into one file + a human-readable summary.

Usage:
    python3 aggregate_findings.py <outdir>

Reads every <outdir>/findings_*.json (the per-chunk verification output), concatenates them
into <outdir>/all_findings.json (each row tagged with its _src file), and prints grouped
counts: REAutor fixes, SPALTE fixes, V/N fixes, title moves, and low/med-confidence entries.

Expected per-finding schema (see AGENT_SPEC.md): title, exists, headword_printed, title_ok,
title_fix, spalte_start_printed, spalte_end_printed, spalte_fix, vorgaenger_printed,
nachfolger_printed, vn_fix, reautor_current, reautor_printed, reautor_fix, confidence, notes.

Use the printed summary to decide the apply/hold split: REAutor + high-confidence single-article
SPALTE are the usual autonomous edits; V/N chain fixes and moves are surfaced for the user.
"""
import sys, glob, os, json


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    outdir = sys.argv[1].rstrip('/')
    rows = []
    for f in sorted(glob.glob(f'{outdir}/findings_*.json')):
        for e in json.load(open(f)):
            e['_src'] = os.path.basename(f)
            # compat: flatten the nested schema ({'reautor': {'ok':..,'printed':..}, ...)
            if isinstance(e.get('reautor'), dict):
                ra = e['reautor']
                if ra.get('ok') is False and ra.get('printed') and not ra.get('multi_author'):
                    e.setdefault('reautor_current', ra.get('current'))
                    e.setdefault('reautor_fix', ra.get('printed'))
                fx = {}
                for k, tag in (('spalte_start', 'SS'), ('spalte_end', 'SE')):
                    v = e.get(k)
                    if isinstance(v, dict) and v.get('ok') is False:
                        fx[tag] = v.get('scan_value')
                if fx:
                    e.setdefault('spalte_fix', fx)
                vn = {}
                for k, tag in (('vorgaenger', 'V'), ('nachfolger', 'N')):
                    v = e.get(k)
                    if isinstance(v, dict) and v.get('ok') is False:
                        vn[tag] = v.get('scan_value')
                if vn:
                    e.setdefault('vn_fix', vn)
                hw = e.get('headword')
                if isinstance(hw, dict) and hw.get('move_target'):
                    e.setdefault('title_fix', hw['move_target'])
            rows.append(e)
    json.dump(rows, open(f'{outdir}/all_findings.json', 'w'), ensure_ascii=False, indent=1)
    print(f'total findings: {len(rows)}\n')

    def show(label, pred, fmt):
        hits = [r for r in rows if pred(r)]
        print(f'=== {label}: {len(hits)}')
        for r in hits:
            print('  ' + fmt(r))
        print()

    show('REAUTOR fixes', lambda r: r.get('reautor_fix'),
         lambda r: f"{r['title']:24} {r.get('reautor_current')!r} -> {r.get('reautor_fix')!r} [{r.get('confidence')}]")
    show('SPALTE fixes', lambda r: r.get('spalte_fix'),
         lambda r: f"{r['title']:24} {r.get('spalte_fix')} [{r.get('confidence')}]  {(r.get('notes') or '')[:70]}")
    show('VN fixes', lambda r: r.get('vn_fix'),
         lambda r: f"{r['title']:24} {r.get('vn_fix')} [{r.get('confidence')}]  {(r.get('notes') or '')[:70]}")
    show('TITLE moves', lambda r: r.get('title_fix'),
         lambda r: f"{r['title']:24} -> {r.get('title_fix')} [{r.get('confidence')}]")
    show('LOW/MED confidence', lambda r: r.get('confidence') in ('low', 'med'),
         lambda r: f"{r['title']:24} [{r.get('confidence')}]  {(r.get('notes') or '')[:90]}")


if __name__ == '__main__':
    main()

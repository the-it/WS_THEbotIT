#!/usr/bin/env python3
"""Build per-subagent assignment chunks for the parallel verification fan-out.

Usage:
    python3 build_chunks.py <outdir> [num_chunks] [scansdir]

Reads <outdir>/all_meta.json + all_wikitext.json (from fetch_wikitext.py) and the PetScan order
(preserved via all_wikitext.json insertion order). Writes <outdir>/chunk_00.json … chunk_NN.json.

num_chunks defaults to 10; scansdir defaults to ".claude_work_dir/scans" (relative to CWD).

Each chunk is a JSON list; per article it carries title, band, spalte_start, spalte_end,
vorgaenger, nachfolger, reautor, is_person, the full wikitext, and start_scan / end_scan =
{page, file (absolute), col, pos} where pos is the column's A/B/C/D position on that spread.
Only start + end spreads are included (a subagent never needs the interior of a long article).

Subagents then read ONLY these local files + crop.py — they have no browser/web access.
"""
import sys, os, json


def scan_page(col):
    return next(P for P in range(col - 1, col + 3) if P % 4 == 1)


def pos_of(col, P):
    return {P - 2: 'A', P - 1: 'B', P: 'C', P + 1: 'D'}.get(col, '?')


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    outdir = sys.argv[1].rstrip('/')
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    scansdir = os.path.abspath(sys.argv[3]) if len(sys.argv) > 3 else os.path.abspath('.claude_work_dir/scans')

    meta = json.load(open(f'{outdir}/all_meta.json'))
    wt = json.load(open(f'{outdir}/all_wikitext.json'))
    order = list(wt.keys())

    def scanfile(prefix, P):
        return f'{scansdir}/{prefix}_{P}.png'

    articles = []
    for t in order:
        if wt.get(t) is None:
            continue
        m = meta[t]
        prefix = (m.get('BAND') or '?').replace(' ', '')
        try:
            ss = int(m['SPALTE_START'])
        except (TypeError, ValueError):
            ss = None
        se_raw = m.get('SPALTE_END')
        se = ss if se_raw in (None, 'OFF', '') else int(se_raw) if se_raw.isdigit() else ss
        entry = {
            'title': t, 'band': m.get('BAND'),
            'spalte_start': m.get('SPALTE_START'), 'spalte_end': m.get('SPALTE_END'),
            'vorgaenger': m.get('VORGÄNGER'), 'nachfolger': m.get('NACHFOLGER'),
            'reautor': m.get('REAutor'), 'is_person': m.get('is_person'),
        }
        if ss is not None:
            Ps, Pe = scan_page(ss), scan_page(se)
            entry['start_scan'] = {'page': Ps, 'file': scanfile(prefix, Ps), 'col': ss, 'pos': pos_of(ss, Ps)}
            entry['end_scan'] = {'page': Pe, 'file': scanfile(prefix, Pe), 'col': se, 'pos': pos_of(se, Pe)}
        entry['wikitext'] = wt[t]
        articles.append(entry)

    per = -(-len(articles) // n)  # ceil
    chunks = [articles[i:i + per] for i in range(0, len(articles), per)]
    for idx, ch in enumerate(chunks):
        json.dump(ch, open(f'{outdir}/chunk_{idx:02d}.json', 'w'), ensure_ascii=False, indent=1)
    print(f'{len(chunks)} chunks, sizes: {[len(c) for c in chunks]}')


if __name__ == '__main__':
    main()

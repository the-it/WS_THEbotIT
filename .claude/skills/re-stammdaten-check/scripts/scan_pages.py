#!/usr/bin/env python3
"""Compute the elexikon scan-page union for a batch (start + end spread per article).

Usage:
    python3 scan_pages.py <outdir>            # reads <outdir>/all_meta.json
    python3 scan_pages.py --cols 42 43 116    # ad-hoc: pages covering these columns

One PNG = a 4-column two-page spread whose page number P ≡ 1 (mod 4) covers columns
P-2 … P+1 laid out A=P-2, B=P-1, C=P, D=P+1. Only the START and END spread of each article
matter (start = exists/headword/Vorgänger; end = SPALTE_END/Nachfolger/signature).

Prints the sorted page list and, per BAND, the filename prefixes (BAND without spaces) so you
know which `<prefix>_<page>.png` files to download.
"""
import sys, json


def scan_page(col):
    return next(P for P in range(col - 1, col + 3) if P % 4 == 1)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    if sys.argv[1] == '--cols':
        cols = [int(c) for c in sys.argv[2:]]
        print(sorted({scan_page(c) for c in cols}))
        return

    outdir = sys.argv[1].rstrip('/')
    meta = json.load(open(f'{outdir}/all_meta.json'))
    by_band = {}
    for t, m in meta.items():
        band = (m.get('BAND') or '?')
        prefix = band.replace(' ', '')
        try:
            ss = int(m['SPALTE_START'])
        except (TypeError, ValueError):
            print(f'  !! {t}: unparseable SPALTE_START={m.get("SPALTE_START")}')
            continue
        se_raw = m.get('SPALTE_END')
        if se_raw in (None, 'OFF', ''):
            se = ss
        else:
            try:
                se = int(se_raw)
            except ValueError:
                se = ss
        by_band.setdefault(prefix, set()).update({scan_page(ss), scan_page(se)})

    total = 0
    for prefix, pages in sorted(by_band.items()):
        total += len(pages)
        print(f'{prefix}: {len(pages)} spreads')
        print('  files:', ' '.join(f'{prefix}_{p}.png' for p in sorted(pages)))
    print(f'total spreads: {total}')


if __name__ == '__main__':
    main()

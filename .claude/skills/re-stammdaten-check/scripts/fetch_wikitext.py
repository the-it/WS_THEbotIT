#!/usr/bin/env python3
"""Bulk-fetch RE article wikitext + extract Stammdaten fields from de.wikisource.

Usage:
    python3 fetch_wikitext.py <petscan.json> <outdir> [--email you@example.com]

<petscan.json> is a PetScan JSON dump (fetched with &format=json&doit=); titles are read
from d['*'][0]['a']['*'][i]['title'] (PetScan gives underscores; the API is queried with
spaces). Alternatively pass a plain .txt file with one title per line.

Writes into <outdir>:
    all_wikitext.json  {title: full_wikitext or null-if-missing}
    all_meta.json      {title: {BAND, SPALTE_START, SPALTE_END, VORGÄNGER, NACHFOLGER,
                                REAutor(first value), n_redaten, n_reautor, is_person}}

Fetches up to 50 titles per POST with a descriptive User-Agent (avoids the 403/429 you get
from looping action=raw at scale). No browser / Cloudflare needed — de.wikisource is plain.
"""
import sys, json, re, time, urllib.request, urllib.parse

API = 'https://de.wikisource.org/w/api.php'


def load_titles(path):
    if path.endswith('.json'):
        d = json.load(open(path))
        items = d['*'][0]['a']['*']
        return [i['title'].replace('_', ' ') for i in items]
    return [ln.strip().replace('_', ' ') for ln in open(path) if ln.strip()]


def post(body, ua):
    req = urllib.request.Request(API, data=urllib.parse.urlencode(body).encode(),
                                 headers={'User-Agent': ua})
    return json.loads(urllib.request.urlopen(req, timeout=60).read())


def field(txt, name):
    m = re.search(r'^\|' + re.escape(name) + r'=(.*)$', txt, re.M)
    return m.group(1).strip() if m else None


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    src, outdir = sys.argv[1], sys.argv[2].rstrip('/')
    email = 'unknown@example.com'
    if '--email' in sys.argv:
        email = sys.argv[sys.argv.index('--email') + 1]
    ua = f'THE-IT-stammdaten-check/1.0 ({email})'

    titles = load_titles(src)
    content = {}
    for i in range(0, len(titles), 50):
        chunk = titles[i:i + 50]
        d = post({'action': 'query', 'prop': 'revisions', 'rvprop': 'content',
                  'rvslots': 'main', 'format': 'json', 'formatversion': '2',
                  'titles': '|'.join(chunk)}, ua)
        for p in d['query']['pages']:
            content[p['title']] = (p['revisions'][0]['slots']['main']['content']
                                   if 'revisions' in p else None)
        time.sleep(0.5)

    json.dump(content, open(f'{outdir}/all_wikitext.json', 'w'), ensure_ascii=False, indent=0)
    missing = [t for t, c in content.items() if c is None]
    print(f'fetched {len(content)} pages; missing: {missing}')

    meta = {}
    for t, c in content.items():
        if c is None:
            continue
        ra = re.search(r'\{\{REAutor\|([^}]*)\}\}', c)
        meta[t] = {
            'BAND': field(c, 'BAND'),
            'SPALTE_START': field(c, 'SPALTE_START'),
            'SPALTE_END': field(c, 'SPALTE_END'),
            'VORGÄNGER': field(c, 'VORGÄNGER'),
            'NACHFOLGER': field(c, 'NACHFOLGER'),
            'REAutor': ra.group(1) if ra else None,
            'n_redaten': len(re.findall(r'\{\{REDaten', c)),
            'n_reautor': len(re.findall(r'\{\{REAutor\|', c)),
            'is_person': 'GEBURTSJAHR' in c,
        }
    json.dump(meta, open(f'{outdir}/all_meta.json', 'w'), ensure_ascii=False, indent=1)
    print(f'meta written for {len(meta)} pages')


if __name__ == '__main__':
    main()

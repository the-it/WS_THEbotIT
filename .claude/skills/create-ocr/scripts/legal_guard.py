#!/usr/bin/env python3
"""Authoritative copyright guard: drop selected pages in a Wikisource:Gemeinfreiheit category.

Usage: legal_guard.py <batch>

Queries prop=categories through the API (catches template-added categories a
text search misses) for every title in <batch>/selected.json, removes hits from
selected.json and records them in skipped.json. Exit 1 if anything was removed.
"""
import argparse
import json
import os
import time
import urllib.parse
import urllib.request

from common import USER_AGENT, WIKISOURCE_API, add_skips, load_json, save_json


def categories(titles):
    cats = {}
    for i in range(0, len(titles), 50):
        body = {"action": "query", "prop": "categories", "cllimit": "max", "format": "json",
                "formatversion": "2", "titles": "|".join(titles[i:i + 50])}
        while True:
            req = urllib.request.Request(WIKISOURCE_API, data=urllib.parse.urlencode(body).encode(),
                                         headers={"User-Agent": USER_AGENT})
            d = json.loads(urllib.request.urlopen(req, timeout=60).read())
            for p in d["query"]["pages"]:
                cats.setdefault(p["title"], []).extend(c["title"] for c in p.get("categories", []))
            if "continue" not in d:
                break
            body.update(d["continue"])
        time.sleep(0.5)
    return cats


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("batch")
    args = ap.parse_args()
    path = os.path.join(args.batch, "selected.json")
    selected = load_json(path)
    cats = categories([c["title"] for c in selected])
    hits = {t: [c for c in cs if "Wikisource:Gemeinfreiheit" in c] for t, cs in cats.items()}
    hits = {t: cs for t, cs in hits.items() if cs}
    keep = [c for c in selected if c["title"] not in hits]
    save_json(path, keep)
    add_skips(args.batch, "legal_guard", [(t, f"legal guard: {', '.join(cs)}") for t, cs in hits.items()])
    print(f"checked {len(selected)}; removed {len(hits)}; {len(keep)} remain")
    for t, cs in hits.items():
        print(f"  REMOVED {t}: {cs}")
    return 1 if hits else 0


if __name__ == "__main__":
    raise SystemExit(main())

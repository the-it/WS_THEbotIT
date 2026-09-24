#!/usr/bin/env python3
"""Fetch the create-ocr PetScan worklist and write titles (spaces, not underscores).

Usage: petscan_titles.py <out_titles.txt> [--json <petscan.json>] [--limit N]

Without --json, queries PetScan live (category RE:Unvollständig minus
Wikisource:Gemeinfreiheit|1 and RE:Stammdaten überprüfen) and stores the raw
response next to the output as petscan.json. --limit keeps the first N titles
(PetScan sorts by title); selection is shortest-first later, so fetch a few hundred.
"""
import argparse
import json
import os
import urllib.request

from common import USER_AGENT, load_json

PETSCAN_URL = (
    "https://petscan.wmcloud.org/?categories=RE%3AUnvollst%C3%A4ndig&depth=1&sortby=title"
    "&language=de&negcats=Wikisource%3AGemeinfreiheit%7C1%0ARE%3AStammdaten%20%C3%BCberpr"
    "%C3%BCfen&project=wikisource&ns%5B0%5D=1&output_compatability=catscan&format=json&doit=")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("out")
    ap.add_argument("--json", help="existing PetScan JSON dump instead of a live query")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    if args.json:
        data = load_json(args.json)
    else:
        req = urllib.request.Request(PETSCAN_URL, headers={"User-Agent": USER_AGENT})
        raw = urllib.request.urlopen(req, timeout=300).read()
        data = json.loads(raw)
        dump = os.path.join(os.path.dirname(os.path.abspath(args.out)), "petscan.json")
        with open(dump, "wb") as fh:
            fh.write(raw)
    titles = [it["title"].replace("_", " ") for it in data["*"][0]["a"]["*"]]
    total = len(titles)
    if args.limit:
        titles = titles[:args.limit]
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write("".join(t + "\n" for t in titles))
    print(f"worklist: {total} titles; wrote {len(titles)} to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Write browser-fetched eLexikon column texts to <batch>/coltext/<BAND>_<col:04d>.txt.

Usage: save_coltexts.py <batch> <result.json> [<result.json> ...]

Each result is a gen_fetch_js.py --kind texts return value ({files, errs}).
Leading U+FEFF is stripped. Empty texts are reported and not written, so
gen_fetch_js.py lists them again (an empty column after a retry means the
column is not digitized: skip the articles on it).
"""
import argparse
import os

from common import load_json


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("batch")
    ap.add_argument("results", nargs="+")
    args = ap.parse_args()
    outdir = os.path.join(args.batch, "coltext")
    os.makedirs(outdir, exist_ok=True)
    written = empty = 0
    for path in args.results:
        data = load_json(path)
        for e in data.get("errs", []):
            print(f"FETCH-ERR  {e}")
        for name, text in data.get("files", {}).items():
            text = (text or "").lstrip("﻿")
            if not text.strip():
                print(f"EMPTY      {name}")
                empty += 1
                continue
            with open(os.path.join(outdir, os.path.basename(name)), "w", encoding="utf-8") as fh:
                fh.write(text)
            written += 1
    print(f"wrote {written} column texts to {outdir}; {empty} empty")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

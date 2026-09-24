#!/usr/bin/env python3
"""Edit pass: save every checked article to de.wikisource as THEbotIT (pywikibot).

Usage: apply_edits.py <batch> [--save] [--only <lemma> ...]

DRY RUN by default: fetches each live page and reports what would be saved.
--save logs in (must be THEbotIT) and saves. Only articles with status PASS or
ALLOWED in <batch>/check_results.json are considered (run run_checks.py first).
Guard per page: the live text must still equal the skel_ref/ snapshot - if
anyone touched the page since the fetch, SKIP and report. One edit per article,
summary common.EDIT_SUMMARY; pywikibot handles conflicts, maxlag and throttle.
Writes <batch>/edit_results.json {lemma: status}. Run with the repo venv python.
"""
import argparse
import os

import pywikibot
from common import EDIT_SUMMARY, load_json, save_json


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("batch")
    ap.add_argument("--save", action="store_true", help="really save (default: dry run)")
    ap.add_argument("--only", nargs="*", help="restrict to these lemmas")
    args = ap.parse_args()
    b = args.batch
    manifest = load_json(os.path.join(b, "manifest.json"))
    checks = load_json(os.path.join(b, "check_results.json"))

    site = pywikibot.Site("de", "wikisource")
    if args.save:
        site.login()
        if site.user() != "THEbotIT":
            raise SystemExit(f"logged in as {site.user()!r}, expected THEbotIT")

    results_path = os.path.join(b, "edit_results.json")
    results = load_json(results_path, default={}) if args.save else {}
    for title, m in manifest.items():
        if args.only and title not in args.only:
            continue
        status = checks.get(title, {}).get("status")
        if status not in ("PASS", "ALLOWED"):
            results[title] = f"NOT_CHECKED_OK: {status}"
            continue
        if args.save and results.get(title) == "SAVED":
            continue
        with open(os.path.join(b, "out", m["fname"] + ".wikitext"), encoding="utf-8") as fh:
            new_text = fh.read()
        with open(os.path.join(b, "skel_ref", m["fname"] + ".wikitext"), encoding="utf-8") as fh:
            skel = fh.read()
        page = pywikibot.Page(site, title)
        if not page.exists():
            results[title] = "SKIP: page missing"
            continue
        if page.text.rstrip("\n") != skel.rstrip("\n"):
            results[title] = "SKIP: live page changed since fetch"
            continue
        if not args.save:
            results[title] = f"WOULD_SAVE ({len(skel)} -> {len(new_text)} chars)"
            continue
        page.text = new_text
        try:
            page.save(summary=EDIT_SUMMARY, minor=False)
            results[title] = "SAVED"
        except Exception as exc:  # noqa: BLE001 - record and continue with the next page
            results[title] = f"ERROR: {exc}"
        save_json(results_path, results)

    if args.save:
        save_json(results_path, results)
    counts = {}
    for v in results.values():
        k = v.split(":")[0].split(" ")[0]
        counts[k] = counts.get(k, 0) + 1
    print(("SAVE" if args.save else "DRY RUN") + ": " + " ".join(f"{k}: {v}" for k, v in sorted(counts.items())))
    for t, v in results.items():
        if not v.startswith(("SAVED", "WOULD_SAVE")):
            print(f"  {t}: {v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

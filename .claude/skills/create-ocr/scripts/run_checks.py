#!/usr/bin/env python3
"""Run check_assembly.py plus batch-level audits over every article of a batch.

Usage: run_checks.py <batch> [--allow-fail <lemma> ...] [--verbose]

For each manifest article: reads out/<f>.notes.json, then checks
out/<f>.wikitext against the CLEAN snapshot skel_ref/<f>.wikitext (never the
subagents' skel/ copy). Extra audits beyond check_assembly.py:
  - <ref> present  -> <references /> must exist and sit after the last {{REAutor}}
  - notes carry a "stammbaum" flag -> listed for the re-stammbaum skill
--allow-fail marks an expected FAIL as accepted (e.g. a Stammbaum plate {{Seite}}
line, which fails "no extra {{Seite templates" by design); apply_edits.py saves
PASS and ALLOWED only.
Writes <batch>/check_results.json {lemma: {status, detail, uncertain, stammbaum}}.
Exit 1 if any FAIL / MISSING remains.
"""
import argparse
import os
import subprocess
import sys

from common import load_json, save_json

CHECK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "check_assembly.py")


def ref_audit(text: str) -> str:
    if "<ref" not in text.replace("<references", ""):
        return ""
    refs = text.rfind("<references")
    if refs < 0:
        return "has <ref> but no <references /> block"
    if refs < text.rfind("{{REAutor|"):
        return "<references /> block sits before {{REAutor}} (move it after)"
    return ""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("batch")
    ap.add_argument("--allow-fail", nargs="*", default=[])
    ap.add_argument("--verbose", action="store_true", help="print full check output for FAILs")
    args = ap.parse_args()
    b = args.batch
    manifest = load_json(os.path.join(b, "manifest.json"))

    results = {}
    for title, m in manifest.items():
        notes_path = os.path.join(b, "out", m["fname"] + ".notes.json")
        new_path = os.path.join(b, "out", m["fname"] + ".wikitext")
        skel_path = os.path.join(b, "skel_ref", m["fname"] + ".wikitext")
        if not os.path.exists(notes_path):
            results[title] = {"status": "MISSING", "detail": "no notes.json (re-spawn)"}
            continue
        notes = load_json(notes_path)
        entry = {"uncertain": notes.get("uncertain", []), "stammbaum": notes.get("stammbaum")}
        if notes.get("status") != "ok":
            results[title] = {**entry, "status": "SKIP", "detail": notes.get("reason", "")}
            continue
        if not os.path.exists(new_path):
            results[title] = {**entry, "status": "MISSING", "detail": "status ok but no .wikitext"}
            continue
        proc = subprocess.run([sys.executable, CHECK, skel_path, new_path],
                              capture_output=True, text=True, check=False)
        fails = [ln for ln in proc.stdout.splitlines() if ln.startswith(("FAIL", "WARN"))]
        with open(new_path, encoding="utf-8") as fh:
            audit = ref_audit(fh.read())
        if audit:
            fails.append(f"FAIL  {audit}")
        failed = proc.returncode != 0 or bool(audit)
        status = "PASS" if not failed else ("ALLOWED" if title in args.allow_fail else "FAIL")
        results[title] = {**entry, "status": status, "detail": "\n".join(fails),
                          "full": proc.stdout if failed and args.verbose else ""}

    save_json(os.path.join(b, "check_results.json"), results)
    counts = {}
    for r in results.values():
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    print(" ".join(f"{k}: {v}" for k, v in sorted(counts.items())) + f"  TOTAL: {len(results)}")
    for title, r in results.items():
        if r["status"] in ("FAIL", "MISSING", "SKIP", "ALLOWED"):
            print(f"\n{r['status']}  {title}\n  " + (r["detail"] or "").replace("\n", "\n  "))
            if r.get("full"):
                print(r["full"])
        elif r["status"] == "PASS" and r["detail"]:
            print(f"\nPASS+WARN  {title}\n  " + r["detail"].replace("\n", "\n  "))
    flagged = [t for t, r in results.items() if r.get("stammbaum")]
    if flagged:
        print("\nStammbaum flagged (work re-stammbaum): " + ", ".join(flagged))
    return 1 if counts.get("FAIL") or counts.get("MISSING") else 0


if __name__ == "__main__":
    raise SystemExit(main())

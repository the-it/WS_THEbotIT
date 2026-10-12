#!/usr/bin/env python3
"""Content audits over the fan-out output, called by run_checks.py (also runnable alone).

Usage: qa_audit.py <batch>

Per article (out/<f>.wikitext against its eLexikon column texts and notes):
  FAIL  bare "|" inside {{Polytonisch|…}} / {{SperrSchrift|…}}: it splits the template
        argument, so the text after it is lost; write {{!}}
  FAIL  notes lack "end_check" (the agent did not confirm on the scan where the article ends)
  WARN  eLexikon <ref name="…"> dropped although its citation is still in the text:
        CIL refs are Wikisource enrichment, not printed footnotes; restore unless the ref
        itself is broken (e.g. a truncated inscription number)
  WARN  eLexikon link / {{RE siehe}} dropped although its display text is still in the text:
        judge by context (correct drops: "Jos." = Book of Joshua, links on fragments of
        unrelated words); an existing target proves nothing
  WARN  ,quote' with comma + apostrophe: the print has ‚…‘
  WARN  the article's segment is the last one on its last column: confirm on the scan that
        the next column opens with a new headword (else SPALTE_END is too small)
Per batch (pairs A -> B where B = A's NACHFOLGER and both are in the batch):
  FAIL  seam overlap: A's body tail occurs in B or B's body head occurs in A (two agents
        cut the same text from a mislabeled eLexikon column)
"""
import argparse
import os
import re

from common import load_json, target_info

REF = re.compile(r'<ref name="([^"]+)">(.*?)</ref>', flags=re.DOTALL)
LINK = re.compile(r"\[\[[^\[\]]+\]\]|\{\{RE siehe\|[^{}]+\}\}")
HEADING = re.compile(r"^== (RE:[^=]+?) ==\s*$", flags=re.MULTILINE)
BAD_QUOTE = re.compile(r"[ (],[A-Za-zÄÖÜäöüß][^',\n]{1,40}'(?!')")


def plain(text: str) -> str:
    """Display text: links -> their label, simple templates -> their argument."""
    text = re.sub(r"<ref.*?</ref>|<ref[^>]*/>", "", text, flags=re.DOTALL)
    text = re.sub(r"\[\[[^\]|]*\|([^\]]*)\]\]", r"\1", text)
    text = re.sub(r"\[\[([^\]]*)\]\]", r"\1", text)
    text = re.sub(r"\{\{RE siehe\|[^|{}]*\|([^|{}]*)[^{}]*\}\}", r"\1", text)
    text = re.sub(r"\{\{RE siehe\|([^|{}]*)\}\}", r"\1", text)
    for _ in range(3):
        text = re.sub(r"\{\{(?:SperrSchrift|Polytonisch|sup)\|([^{}]*)\}\}", r"\1", text)
    return re.sub(r"\s+", " ", text)


def link_target(link: str) -> str:
    inner = link[2:-2]
    if inner.startswith("RE siehe|"):
        return inner.split("|")[1]
    return inner.split("|")[0]


def still_linked(target: str, out: str) -> bool:
    """The target is linked somewhere in out (display text may have been corrected)."""
    return any(s in out for s in (f"[[{target}|", f"[[{target}]]", f"{{{{RE siehe|{target}|",
                                  f"{{{{RE siehe|{target}}}}}"))


def link_display(link: str) -> str:
    inner = link[2:-2]
    if inner.startswith("RE siehe|"):
        parts = inner.split("|")
        return parts[2] if len(parts) > 2 else parts[1]
    return plain(inner.split("|")[-1])


def template_spans(text: str, name: str):
    """Yield the inner argument text of every {{name|…}}, nesting-aware."""
    for m in re.finditer(r"\{\{" + name + r"\|", text):
        depth, i = 0, m.start()
        while i < len(text):
            if text.startswith("{{", i):
                depth, i = depth + 1, i + 2
            elif text.startswith("}}", i):
                depth, i = depth - 1, i + 2
                if depth == 0:
                    break
            else:
                i += 1
        yield text[m.end():i - 2]


def bare_pipes(text: str):
    hits = []
    for name in ("Polytonisch", "SperrSchrift"):
        for inner in template_spans(text, name):
            flat = re.sub(r"\[\[[^\]]*\]\]", "", inner)
            while re.search(r"\{\{[^{}]*\}\}", flat):
                flat = re.sub(r"\{\{[^{}]*\}\}", "", flat)
            if "|" in flat:
                hits.append(f"{{{{{name}|{inner[:60]}…}}}}")
    return hits


def body_of(text: str) -> str:
    try:
        info = target_info(text.replace("KORREKTURSTAND=unkorrigiert", "KORREKTURSTAND=unvollständig", 1))
    except ValueError:
        return text
    return "\n".join(info["body"])


def article_audit(batch: str, m: dict, out: str, notes: dict):
    """[(level, message)] for one article."""
    found = []
    for hit in bare_pipes(out):
        found.append(("FAIL", f"bare | inside template (write {{{{!}}}}): {hit}"))
    if "end_check" not in notes:
        found.append(("FAIL", "notes lack end_check (where does the article end on the scan?)"))
    pout = plain(out)
    for col in m["cols"]:
        path = os.path.join(batch, "coltext", f"{m['band']}_{int(col):04d}.txt")
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as fh:
            ct = fh.read()
        for r in REF.finditer(ct):
            before = plain(ct[max(0, r.start() - 200):r.start()])[-25:]
            if before.strip() and before in pout and f'name="{r.group(1)}"' not in out:
                found.append(("WARN", f"dropped <ref {r.group(1)}> after …{before.strip()}"))
        for lm in LINK.finditer(ct):
            link = lm.group(0)
            if link in out or still_linked(link_target(link), out):
                continue
            disp = link_display(link).strip()
            before = plain(ct[max(0, lm.start() - 120):lm.start()])[-20:]
            if len(disp) > 1 and before.strip() and (before + disp) in pout:
                found.append(("WARN", f"dropped link {link}"))
        heads = HEADING.findall(ct)
        if col == m["cols"][-1] and heads and heads[-1] == m["title"]:
            found.append(("WARN", (f"last segment on col {col}: confirm col {int(col) + 1} opens "
                                   "with a new headword")))
    for q in BAD_QUOTE.finditer(body_of(out)):
        found.append(("WARN", f"quote {q.group(0).strip()!r}: print has ‚…‘"))
    return found


def norm(text: str) -> str:
    return re.sub(r"[^\w]", "", plain(re.sub(r"^\{\{Seite\|.*$", " ", text, flags=re.MULTILINE)).lower())


def seam_audit(bodies: dict, nachfolger: dict):
    """{title: [(level, message)]} for overlapping cuts between batch neighbours."""
    found = {}
    for a, b in nachfolger.items():
        if a not in bodies or b not in bodies:
            continue
        na, nb = norm(bodies[a]), norm(bodies[b])
        tail, head = na[-40:], nb[8:48]
        if (len(tail) >= 20 and tail in nb) or (len(head) >= 20 and head in na):
            found.setdefault(a, []).append(("FAIL", f"seam overlap with successor {b} (same text cut twice?)"))
    return found


def batch_audit(batch: str, manifest: dict):
    """{title: [(level, message)]} for every article with an out/ text."""
    results, bodies, nachfolger = {}, {}, {}
    for title, m in manifest.items():
        out_path = os.path.join(batch, "out", m["fname"] + ".wikitext")
        notes_path = os.path.join(batch, "out", m["fname"] + ".notes.json")
        if not os.path.exists(out_path) or not os.path.exists(notes_path):
            continue
        with open(out_path, encoding="utf-8") as fh:
            out = fh.read()
        results[title] = article_audit(batch, {**m, "title": title}, out, load_json(notes_path))
        bodies[title] = body_of(out)
        with open(os.path.join(batch, "skel_ref", m["fname"] + ".wikitext"), encoding="utf-8") as fh:
            nf = re.search(r"^\|NACHFOLGER=(.+)$", fh.read(), flags=re.MULTILINE)
        if nf:
            nachfolger[title] = "RE:" + nf.group(1).strip()
    for title, hits in seam_audit(bodies, nachfolger).items():
        results[title].extend(hits)
    return results


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("batch")
    args = ap.parse_args()
    results = batch_audit(args.batch, load_json(os.path.join(args.batch, "manifest.json")))
    fails = 0
    for title, hits in results.items():
        if hits:
            print(f"### {title}")
            for level, msg in hits:
                print(f"  {level}  {msg}")
                fails += level == "FAIL"
    print(f"{sum(len(h) for h in results.values())} findings, {fails} FAIL")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())

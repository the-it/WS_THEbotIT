"""Shared helpers for the create-ocr batch scripts.

Batch directory layout (every script takes the batch dir as first argument):

    <batch>/titles.txt            worklist titles, one per line
    <batch>/all_wikitext.json     fetch_wikitext.py output {title: wikitext}
    <batch>/all_meta.json         fetch_wikitext.py output
    <batch>/selected.json         select_candidates.py / legal_guard.py
    <batch>/skipped.json          every skip with its reason (appended by each stage)
    <batch>/manifest.json         build_manifest.py
    <batch>/skel_ref/<f>.wikitext clean skeleton snapshot (never handed to subagents)
    <batch>/skel/<f>.wikitext     subagent working copy of the skeleton
    <batch>/fetch_js/*.js         gen_fetch_js.py (paste into browser_evaluate)
    <batch>/coltext/<BAND>_<col:04d>.txt   save_coltexts.py
    <batch>/scans/<BAND>_<col:04d>.png     decode_b64_files.py
    <batch>/chunks/chunk_NN.json, prompts.json   build_chunks.py
    <batch>/out/<f>.wikitext, <f>.notes.json      subagent output
    <batch>/check_results.json    run_checks.py
    <batch>/stammdaten_fixes.json, stammdaten_results.json   fix_stammdaten.py
    <batch>/edit_results.json     apply_edits.py
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from check_assembly import redaten_blocks, target_block  # noqa: F401

WIKISOURCE_API = "https://de.wikisource.org/w/api.php"
USER_AGENT = "THEbotIT-create-ocr/1.0 (https://de.wikisource.org/wiki/Benutzer:THEbotIT)"
EDIT_SUMMARY = ("OCR-Text von elexikon.ch eingefügt und am Scan korrekturgelesen, "
                "Korrekturstand: unkorrigiert")
SEITE_RE = re.compile(r"\{\{Seite\|[^{}\n]*(?:\{\{[^{}\n]*\}\}[^{}\n]*)*\}\}")


def fname(lemma: str) -> str:
    """File stem for a lemma: 'RE:Foo 2' -> 'RE_Foo 2'. Keeps non-ASCII (no collisions)."""
    return lemma.replace("/", "_").replace(":", "_")


def col_key(band: str, col: int) -> str:
    """Local file stem for one printed column: 'VII A,1', 752 -> 'VII A,1_0752'."""
    return f"{band}_{int(col):04d}"


def scan_dir_letter(band: str) -> str:
    """eLexikon scan sub-directory: 'S' for Supplements, half-band letter, else '_'."""
    if band.startswith("S "):
        return "S"
    m = re.match(r"^[IVXL]+ ([A-Z]),", band)
    return m.group(1) if m else "_"


def span_of(start, end) -> int:
    """Column span from raw SPALTE_START/SPALTE_END values (raises ValueError)."""
    s = int(str(start).strip())
    e = str(end or "").strip()
    return 1 if e in ("", "OFF") else int(e) - s + 1


def load_json(path, default=None):
    if default is not None and not os.path.exists(path):
        return default
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    if isinstance(data, str):  # browser_evaluate filename: output can be re-quoted JSON
        data = json.loads(data)
    return data


def save_json(path, data) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=1)


def add_skips(batch: str, stage: str, skips) -> None:
    """Append [(title, reason), ...] to <batch>/skipped.json, tagged with the stage."""
    path = os.path.join(batch, "skipped.json")
    existing = load_json(path, default=[])
    existing.extend({"title": t, "stage": stage, "reason": r} for t, r in skips)
    save_json(path, existing)


def field(block_lines, name):
    """Value of |NAME=... inside a REDaten block (list of lines), or None."""
    prefix = f"|{name}="
    for line in block_lines:
        if line.startswith(prefix):
            return line[len(prefix):].strip()
    return None


def target_info(text: str):
    """Locate the single unvollständig block. Returns dict or raises ValueError(reason)."""
    lines = text.splitlines()
    blocks = [(s, e) for s, e in redaten_blocks(lines)
              if "|KORREKTURSTAND=unvollständig" in (x.strip() for x in lines[s:e + 1])]
    if len(blocks) != 1:
        raise ValueError(f"{len(blocks)} unvollständig blocks (need exactly 1)")
    start, end = blocks[0]
    block = lines[start:end + 1]
    autor = next((i for i in range(end + 1, len(lines)) if "{{REAutor|" in lines[i]), None)
    if autor is None:
        raise ValueError("no {{REAutor}} after target block")
    return {
        "lines": lines,
        "block_start": start,  # index of the "{{REDaten" line
        "body_start": end + 1,  # first line after the block's closing "}}"
        "autor_line": autor,  # index of the block's {{REAutor}} line
        "block": block,
        "body": lines[end + 1:autor],
        "band": field(block, "BAND"),
        "spalte_start": field(block, "SPALTE_START"),
        "spalte_end": field(block, "SPALTE_END"),
        "nachtrag": field(block, "NACHTRAG"),
        "todesjahr": field(block, "TODESJAHR"),
    }


def body_is_pristine(body_lines) -> str:
    """'' if the body is headword + [...] + Seite lines only, else a reason string."""
    if not any(line.strip() == "[...]" for line in body_lines):
        return "no [...] placeholder line - already started"
    for line in body_lines:
        s = line.strip()
        if not s or s == "[...]" or SEITE_RE.fullmatch(s):
            continue
        if s.startswith(":") and "zum Art." in s:  # Nachtrag lead-in
            continue
        if re.fullmatch(r"'''.*?'''\s*:?", s):  # bold headword ('''Foo''', '''2)''')
            continue
        return f"unexpected body content: {s[:60]!r}"
    return ""

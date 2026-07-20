---
name: create-ocr
description: >-
  Fill incomplete ("unvollständig") RE (Pauly Realencyclopädie) articles on de.wikisource
  with the enriched OCR text from elexikon.ch: fetch the article's OCR wikitext and the
  column scans, proofread the text word-by-word against the scans, insert it page by page
  keeping the {{Seite|…}} separators, and set KORREKTURSTAND to "unkorrigiert". Use whenever
  the user wants to create/insert OCR for RE articles, fill unvollständig RE articles, work
  through the "RE:Unvollständig" category/PetScan worklist, or says "create OCR" for RE
  lemmas.
---

# RE create-OCR — fill "unvollständig" articles from eLexikon

An *unvollständig* RE article on **de.wikisource.org** is a metadata skeleton: a
`{{REDaten}}` block, the bold headword, a `[...]` placeholder, pre-generated
`{{Seite|…}}` column separators, `{{REAutor|…}}`, and categories. This skill replaces the
placeholder with the **eLexikon enriched OCR text**, proofread **word-by-word against the
printed column scans**, and flips `KORREKTURSTAND=unvollständig` → `unkorrigiert`.
Everything else in the skeleton (Stammdaten, `{{Seite}}` lines, `{{REAutor}}`, categories)
stays byte-identical.

## Shared machinery — reuse `re-stammdaten-check`

Read `../re-stammdaten-check/SKILL.md` for the infrastructure and reuse it; don't
re-derive:

- **Edits:** the edit pass runs as the bot account **THEbotIT** via **pywikibot** — see
  "Making edits (pywikibot as THEbotIT)" in the stammdaten skill. No browser login is
  needed for wikisource at all; the Playwright browser is only used to reach eLexikon
  (no login there either, just the Cloudflare clearance below). Playwright MCP tools are
  deferred — load them with ToolSearch.
- **Reading wikisource:** not behind Cloudflare — `curl …action=raw` for a few pages,
  bulk via the query API (50 titles/POST, descriptive User-Agent). PetScan gives titles
  with underscores, the API returns spaces.
- **elexikon.ch is behind Cloudflare:** only the browser session can fetch from it (curl
  fails even with the cookie — TLS fingerprinting). Navigate once to any elexikon page,
  `browser_wait_for {time: 6}`; after that, in-page `fetch(url, {credentials:'include'})`
  works for every elexikon URL. On ~3 consecutive 403s, re-navigate + wait 10 and resume.
- `../re-stammdaten-check/scripts/fetch_wikitext.py` (bulk wikitext+meta) and
  `scripts/crop.py` (zoom into a scan region) are used below.

## Worklist & scope

- **Source:** PetScan — category `RE:Unvollständig`, **minus** everything under
  `Wikisource:Gemeinfreiheit` (depth 1) **and** `RE:Stammdaten überprüfen`, dewikisource ns 0:
  `https://petscan.wmcloud.org/?categories=RE%3AUnvollst%C3%A4ndig&depth=1&sortby=title&language=de&negcats=Wikisource%3AGemeinfreiheit%7C1%0ARE%3AStammdaten%20%C3%BCberpr%C3%BCfen&project=wikisource&ns%5B0%5D=1&output_compatability=catscan&format=json&doit=`
  (results at `d['*'][0]['a']['*']`, each item has `title`; ~14 000 entries as of 2026-07;
  negcats are **newline-separated** — `%0A` in the URL — and a `|1` suffix sets that cat's depth).
- The `Wikisource:Gemeinfreiheit` negcat is a **copyright guard**: articles in a
  `Wikisource:Gemeinfreiheit <year>` subcategory have authors not yet 71 years dead — their text
  must NOT be published. Never work on a lemma outside this filtered list, and re-check the guard
  per article (below) if the user hands you lemmas directly.
- The `RE:Stammdaten überprüfen` negcat **excludes articles whose metadata isn't verified yet**:
  their auto-generated `SPALTE_*`/`BAND` can be wrong, which makes the OCR insert fail (the
  scan column doesn't match, the article spans a column you didn't fetch, etc. — the exact cause
  of the skips in batch 2026-07-18). Let those go through `re-stammdaten-check` first.
- **Ask the user how many articles to work on if they didn't say.** If they named
  specific lemmas, use those.
- **Selection: shortest first.** Bulk-fetch the wikitext of the first few hundred
  worklist titles (`fetch_wikitext.py` accepts a one-title-per-line `.txt`), compute the
  column span (`1` if `SPALTE_END=OFF`, else `END−START+1`), and take the N shortest that
  pass the per-article guards. Short articles = few columns = quick proofreads.
  (On this Mac the python.org Python lacks CA certs — run the fetch with
  `SSL_CERT_FILE=/Library/Frameworks/Python.framework/Versions/3.13/lib/python3.13/site-packages/certifi/cacert.pem`.)

### Per-article guards (skip & report instead of forcing)

1. **Pristine skeleton:** the body is exactly the bold headword line, a `[...]` line, the
   `{{Seite|…}}` lines, `{{REAutor|…}}`, categories. If there's already real text or no
   `[...]`, someone started filling it — skip.
2. **Exactly one `{{REDaten}}` block** and `NACHTRAG=OFF`. Multi-band/Nachtrag pages have
   several chains on one page — out of scope, skip.
3. `KORREKTURSTAND=unvollständig` (still).
4. **Legal guard:** the page's categories (query `prop=categories`) contain no
   `Kategorie:Wikisource:Gemeinfreiheit…`. If one is there, do not fill the article,
   whatever the worklist said.
5. `VERWEIS=ON` articles are fine (tiny bodies like `'''2) s. Turba.'''`).

## eLexikon endpoints (what to fetch)

- **Whole-article enriched text (primary):** `https://elexikon.ch/?Typ=REt&Text=<lemma>`
  with the wikisource lemma minus the `RE:` prefix, spaces→underscores (`Tuba_2`,
  `Tubantes`). The content is the **last `<pre>` inside `div.ml15`** (the first `<pre>` is
  a nav bar). It is ready wikitext: `[[links]]`, `{{RE siehe|…}}`, `{{Polytonisch|…}}`,
  `{{SperrSchrift|…}}`, `''italics''` — **and `{{Seite|N}}` lines already placed at the
  exact column breaks**. The first line is a `RE:<lemma>` heading (drop it), and the
  printed end-signature `[…]` is already stripped (the skeleton's `{{REAutor}}` carries
  it — never re-add it to the body).
- **Per-column text (fallback):** `https://elexikon.ch/?Typ=REt&Text=<BAND-no-space>_<col>`
  (e.g. `VIIA,1_749`; the padded space form `VII+A,1_0749` also works). One printed column
  per page, article boundaries marked by `== RE:<lemma> ==` headings. Use when the
  by-lemma fetch fails or its `{{Seite}}` breaks don't match the skeleton.
- **Column scans (for proofreading):**
  `https://elexikon.ch/meyers/REo/<dir>/<BAND>_<col %04d>.png` — one printed column per
  PNG (≈700–1000 px wide, full column height). `<dir>` is the **half-band letter**: `A`
  for `BAND=VII A,1` (→ `/meyers/REo/A/VII%20A,1_0752.png`, URL-encode the space), `_`
  for letterless bands like `BAND=VIII,1` (→ `/meyers/REo/_/VIII,1_0664.png`). If unsure,
  open `/?Typ=REo&Text=<BAND>_<col %04d>` once and read the `<img src>`. Fetch one PNG
  per column in `[SPALTE_START … SPALTE_END]`.
- **4-column spreads (context fallback):** `https://elexikon.ch/meyers/RE/<BAND-no-space>_<P>.png`
  with `P ≡ 1 (mod 4)` covering columns `P−2 … P+1` (see the stammdaten skill).

### Bulk-fetch pattern (main session, one `browser_evaluate` loop)

Subagents cannot reach elexikon — **pre-fetch everything to local files**, then fan out.
In one evaluate call, loop the articles (~700 ms pacing), save the results with the
`filename:` parameter so multi-MB blobs never enter your context:

- *Texts:* `fetch(url, {credentials:'include'})` → `DOMParser` →
  `[...doc.querySelectorAll('div.ml15 pre')].pop().textContent` → return `{lemma: text}`.
- *Scans:* `fetch` → `arrayBuffer` → base64 (chunk `String.fromCharCode` in ~8 KB slices)
  → return `{"<BAND>_<col %04d>.png": b64}`; decode locally with
  `scripts/decode_b64_files.py <batch.json> <scansdir>`.

## Assembly (per article)

Build the new page text from three parts, in place of the skeleton's headword + `[...]`
lines:

1. eLexikon body: drop the `RE:<lemma>` heading line and strip BOM/zero-width chars
   (U+FEFF — one hides at the start of each column's text). The nav bar is the other
   `<pre>` and never part of the extract.
2. **Replace each eLexikon `{{Seite|N}}` line with the skeleton's exact `{{Seite|…}}`
   line for that N** — odd columns carry a `{{REIA|…}}` scan-link parameter that must
   survive (`{{Seite|753||{{REIA|VII A,1|753}}}}`). Every skeleton `{{Seite}}` line must
   be used exactly once, in order. A count/number mismatch usually means the skeleton's
   `SPALTE_*` values and eLexikon disagree — don't force it; verify against the scan,
   note it in the report, and skip (Stammdaten fixes belong to `re-stammdaten-check`).
   Keep the `{{Seite}}` lines on their own line inside the running paragraph (no blank
   lines around them unless the print has a paragraph break there); if a word is
   hyphen-split across the column break, join it on the side where the larger part sits.
3. Everything else byte-identical: the `{{REDaten}}` block with **only**
   `KORREKTURSTAND=unvollständig` → `unkorrigiert` changed, then the proofread body, then
   `{{REAutor|…}}` and all trailing `[[Kategorie:…]]` lines unchanged (never remove
   maintenance categories — the user handles those).
4. **Footnotes:** some eLexikon texts carry `<ref>…</ref>` tags plus a trailing
   `== Anmerkungen (Wikisource) ==` / `<references />` block. Keep the ref tags in the
   body, but move the Anmerkungen block to **after** `{{REAutor|…}}` (before any
   `[[Kategorie:…]]` lines) — that's where corrected RE articles put it (cf.
   `RE:Apollodoros 61`). Watch for OCR damage *inside* templates too, e.g. a
   `{{SperrSchrift|M. He-}}rennius` split mid-word by a line-break hyphen.

The opening bold headword comes from eLexikon **as printed** (e.g.
`'''Tubantes''' (im laterculus …`) and replaces the skeleton's bare `'''Tubantes'''` line.

## Proofread word-by-word against the scans

The target state is *unkorrigiert*, but the user wants a **full proofread** while
inserting: read every column PNG next to the text and make the text match the print
exactly. The column PNGs are legible but small — crop them into 3–4 vertical strips and
upscale with `../re-stammdaten-check/scripts/crop.py <png> 0 0.0 <img-width> 0.3 <out.png> 2`
(x in pixels — use the PNG's real width, it varies by band; y as height fractions).

Systematic OCR artifacts, all seen in real output — hunt for each:

- **Margin line-counters swallowed into the text.** The print numbers every 10th line
  (10, 20, … 60) in the column margin; OCR drops them mid-sentence
  (`Auf ''Tubanti'' führt 10 {{Polytonisch|Τούβαντοί}}`), sometimes mangled (`4·` for 40).
  Delete them — but confirm on the scan first: RE text is full of genuine numbers.
- **Hyphen line-breaks kept:** `Na-menb.`, `Germanen-stamm`, `Tam-fana` → rejoin per the
  scan (keep genuine hyphens).
- **False paragraph breaks** (blank line where the print runs on) → rejoin. Real
  paragraph breaks are rare in RE; long articles may have bold section heads — render
  those as `{{Überschrift|…}}` like corrected articles do.
- **Misreads**, Latin and especially Greek: `Reailex,`→`Reallex.`, `eich`→`sich`,
  `Genn.`→`Germ.`, `85fL`→`85ff.`, `Strab»`→`Strab.`. Verify every `{{Polytonisch|…}}`
  **letter by letter including breathings/accents** on a zoomed crop — OCR Greek is
  unreliable (`ὀάλπιγξ` where the print has `σάλπιγξ`), and Roman numerals get misread as
  Greek (`{{Polytonisch|CXIλΧΠ}}` for a printed `CXLVII`). A misspelled Greek word is a
  real error someone else has to find later — don't type Greek from memory.
- **Letter-spaced (gesperrt) names left raw:** `C a r t n e y`, `Bruss-k e r n` →
  `{{SperrSchrift|McCartney}}`-style per the scan, matching how eLexikon marks the others.
- Punctuation: `,low quotes‘`, dashes, `»«` — match the print.

**Keep the enrichment.** The `[[…|…]]` links, `{{RE siehe|…}}`, `#Seite_…` anchors and
italics are curated added value; the rule is that the **displayed text** must match the
print exactly. Fix display text inside links rather than deleting the link; don't invent
new links; drop a link only if its display text cannot be made to match the print.

## Fan-out: one subagent per article, max 10 subagents

Subagents work **offline only** — local files + `crop.py`; no browser, no web, no wiki
edits (there is only one browser session, and it belongs to the main loop). **Always spawn
the subagents with the `sonnet` model** (pass `model: "sonnet"` to the Agent tool for every
fan-out subagent). **Never spawn
more than 10 subagents in total for a batch.** Up to 10 articles: one subagent per
article. More than 10: split the articles into at most 10 chunks (round-robin or
contiguous, ~⌈N/10⌉ articles each) and give each subagent its whole chunk to process
sequentially. Give each subagent, per article: the skeleton wikitext path, the eLexikon
text path, the column PNG paths, and the article meta (lemma, BAND, SPALTE_START/END).
For each article the subagent writes:

- `<workdir>/out/<lemma>.wikitext` — the complete new page text, and
- `<workdir>/out/<lemma>.notes.json` —
  `{lemma, status: "ok"|"skip", reason, uncertain: ["col 753: Greek accent on …"], fixes: {line_numbers, hyphens, misreads, paragraph_joins}}`.

Subagents die on transient API errors; the output files are the source of truth — re-spawn
for any articles whose files are missing (idempotent, still within the 10-subagent cap).
Parallel is fine.

## Structural check before saving

Run `scripts/check_assembly.py <skeleton.wikitext> <new.wikitext>` for **every** article.
It verifies mechanically what a tired eye skips: the REDaten diff is exactly the
KORREKTURSTAND flip, all `{{Seite}}` lines survive byte-identically in order, REAutor and
categories are intact, no `[...]`/BOM/`== RE:` heading remains, and the body length is
plausible for the column count. Fix any FAIL before the edit pass; treat WARNs as review
pointers.

## Edit pass (main session, sequential, pywikibot as THEbotIT)

Edits run as **THEbotIT** through pywikibot (repo venv + `~/.pywikibot/user-config.py`
OAuth — see the stammdaten skill's "Making edits" section for the pattern and how to run
the script). Put the edit script in `.claude_work_dir`, feed it the `out/` directory, and
process each article in **one edit** (never split):

1. `page = pywikibot.Page(site, lemma)`; **guard:** `page.exists()` and `page.text` still
   contains the `[...]` line and `KORREKTURSTAND=unvollständig` — otherwise someone
   touched it meanwhile: SKIP and report.
2. Set `page.text` to the full new text and `page.save(summary=..., minor=False)` with
   summary
   `OCR-Text von elexikon.ch eingefügt und am Scan korrekturgelesen, Korrekturstand: unkorrigiert`.
   pywikibot handles edit conflicts (basetimestamp), `maxlag=5`, and pacing
   (`put_throttle=2`) itself.

## Verify & report

Re-fetch each edited page: `KORREKTURSTAND=unkorrigiert`, no `[...]`, categories now show
`RE:Unkorrigiert` (not `RE:Unvollständig`). Then hand the user a written report — a table
`lemma | columns | fixes (line-nrs/hyphens/misreads) | uncertainties | status` plus the
skipped articles with reasons. Flag any suspected Stammdaten problems (wrong SPALTE,
odd V/N) for a `re-stammdaten-check` pass instead of fixing them here.

## Gotchas

- **eLexikon lemma key ≠ wikisource lemma** (rare; Greek titles, special chars): if the
  by-lemma URL misses, open the per-column page of `SPALTE_START` — its nav bar links
  "show this Article completely" with eLexikon's own key for the lemma.
- **Article not digitized / empty text** on eLexikon → skip & report.
- **`{{Seite}}` mismatch = probable Stammdaten error** — never "fix" SPALTE here; report.
- **Do not touch** VORGÄNGER/NACHFOLGER, SORTIERUNG, KURZTEXT, maintenance categories, or
  anything else in the skeleton beyond the KORREKTURSTAND flip and the body.
- The state goes to **unkorrigiert** even after a full proofread — wikisource's
  correction workflow needs an independent second reader for *korrigiert*.

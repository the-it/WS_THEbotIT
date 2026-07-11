---
name: re-stammdaten-check
description: >-
  Double-check the metadata (Stammdaten) of RE (Pauly Realencyclopädie) articles on
  de.wikisource against the printed elexikon.ch scans: verify column/Vorgänger/Nachfolger,
  correct REAutor to the exact printed signature, move Greek-headword lemmas to their Greek
  title, and stage each batch for the user's final review. Use when the user wants to check /
  verify RE articles, work through the "RE:Stammdaten überprüfen" maintenance category, or
  process the RE Stammdaten PetScan worklist.
---

# RE Stammdaten-Check

Verify the auto-generated metadata of RE articles on **de.wikisource.org** against the
original printed scans, fix what's wrong, and stage a batch for the user to review. The
articles are regenerated nightly from register data, so their Stammdaten can be wrong until a
human checks them against the scan.

## Worklist & references

- **Articles to work on:** PetScan `https://petscan.wmcloud.org/?psid=48501612`
  (add `&format=json&doit=`; results are at `d['*'][0]['a']['*']`, each item has `title`).
- **What to check (canonical):** the category page
  `https://de.wikisource.org/wiki/Kategorie:RE:Stammdaten_überprüfen`.
- **Scans:** elexikon.ch, e.g. `https://elexikon.ch/meyers/RE/VIIA,1_525.png`.
- Full editor guide: `Wikisource:RE-Werkstatt/Anleitung`.

## Prerequisites

- The user logs Claude in through the **Playwright browser** (their personal account, e.g.
  "THE IT" — *not* the THEbotIT bot). All edits/moves go through that browser session.
  Just navigate to `https://de.wikisource.org` and ask them to log in; verify via a snapshot
  of the "Persönliche Werkzeuge" nav.
- The Playwright MCP tools are deferred — load them with ToolSearch
  (`browser_navigate`, `browser_take_screenshot`, `browser_evaluate`, `browser_wait_for`,
  `browser_snapshot`, and `browser_run_code_unsafe` for grabbing the elexikon cookie).

## What to verify against the scan (per article)

1. **Exists** at that RE issue (BAND + column).
2. **SPALTE_START / SPALTE_END** correct. `SPALTE_END=OFF` means single column (start == end).
   For multi-column articles, find the end by browsing the scans. `SPALTE_END` is the column
   holding the article's **last line of text**: if the article ends flush at the bottom of a
   column and the next lemma opens the following column, it does **not** extend into that next
   column — set `SPALTE_END` to the ending column (`OFF` if that equals the start). The nightly
   ReScanner tends to over-count the end by one in exactly this column-break case, so check it.
3. **VORGÄNGER / NACHFOLGER** are really the articles printed before/after — verify with the
   scan. (See the Nachtrag/band-chain gotcha below; don't over-eagerly "fix" these.)
4. **REAutor** = the **exact** signature printed in `[ ... ]` at the article's end
   (see "REAutor" below). Short articles may share the *next* signed article's author; pure
   redirects/verweise get `{{REAutor|OFF}}`.

## Getting the article wikitext

de.wikisource is **not** behind Cloudflare — plain curl works:

```bash
curl -s "https://de.wikisource.org/w/index.php?title=RE:Troadesier&action=raw"
```

For metadata across several articles, grep the fields:

```bash
curl -s ".../index.php?title=<urlenc>&action=raw" \
  | grep -iE "BAND=|SPALTE_START=|SPALTE_END=|VORGÄNGER=|NACHFOLGER=|KURZTEXT=|REAutor|Kategorie:RE:Stammdaten"
```

**At scale (dozens/hundreds of lemmas), don't loop `action=raw`** — it gets HTTP 429
("your bot is making too many requests") after ~50 hits, and `urllib` without a `User-Agent`
gets 403. Instead fetch in bulk via the query API, **up to 50 titles per POST**, with a
descriptive UA:

```python
import urllib.request, urllib.parse, json
UA = 'THE-IT-stammdaten-check/1.0 (<your-email>)'
def post(body):
    req = urllib.request.Request('https://de.wikisource.org/w/api.php',
        data=urllib.parse.urlencode(body).encode(), headers={'User-Agent': UA})
    return json.loads(urllib.request.urlopen(req, timeout=60).read())
d = post({'action':'query','prop':'revisions','rvprop':'content','rvslots':'main',
          'format':'json','formatversion':'2','titles':'|'.join(chunk_of_50)})
# content: d['query']['pages'][i]['revisions'][0]['slots']['main']['content']
# note: API returns titles with SPACES; PetScan gives them with UNDERSCORES.
```

## Getting the scans (elexikon.ch)

- **elexikon.ch IS behind Cloudflare** — plain curl returns a "Just a moment…" challenge
  page. You **must** load scans in the Playwright browser. The `cf_clearance` cookie persists
  for a while but expires; if a navigation returns HTTP 403 / title "Just a moment…", call
  `browser_wait_for {time: 6}` and re-screenshot.
- **One PNG = a 4-column two-page spread.** E.g. `VIIA,1_525.png` shows columns **523–526**;
  `_585.png` shows 583–586; spreads step by 4 (…_585, _589, _593, _597, _601…). So a handful
  of scans cover a whole batch — dedupe the scan list and read each spread once.
- **Compute the scan filename from the metadata — don't do a per-page `externallinks` lookup**
  (that's slow and rate-limited at scale). Filename = `<BAND-without-spaces>_<page>.png`, so
  `BAND=VII A,1` → `VIIA,1_…`, `BAND=VII A,2` → `VIIA,2_…` (**a page can hold both bands — always
  use each article's own `BAND=`, never assume one prefix for the batch**). The page number for
  a column `C` is the unique `P ≡ 1 (mod 4)` in `[C−1, C+2]`; that spread covers columns
  `P−2 … P+1`, laid out left→right **A=P−2, B=P−1 | C=P, D=P+1**:

  ```python
  def scan_page(col):            # e.g. 525 -> 525, 523 -> 525, 527 -> 529
      return next(P for P in range(col-1, col+3) if P % 4 == 1)
  pages = sorted({scan_page(c) for c in range(spalte_start, spalte_end+1)})
  ```

  (If in doubt, the authoritative source is still the rendered page's `externallinks`: the
  `…_NNN.png` links are the "Bildergalerie im Original".)
- **Downloading many scans efficiently (native resolution).** curl with the `cf_clearance`
  cookie **fails** — Cloudflare also fingerprints the TLS/JA3, so only the *browser* can fetch.
  But you do **not** have to screenshot each one:
  1. Navigate to **one** scan, then `browser_wait_for {time: 6}` so Cloudflare fully solves the
     challenge. This makes clearance **global for the session** — after that, `fetch()` for any
     other scan URL returns 200 (a fresh navigation alone, before the wait, is not enough).
  2. In a single `browser_evaluate`, loop the needed pages, `fetch()` each PNG same-origin,
     base64-encode the `arrayBuffer`, and return them joined; save with the `filename:` param so
     the (multi-MB) blob lands in a file **instead of your context**. Pace ~300 ms between
     fetches (bursts get rate-limited; retry the misses in a second pass). Then base64-decode
     locally to real `.png` files. Native size is **3685×2592** (higher res than a screenshot).
     Grab the cookie/UA once via `browser_run_code_unsafe` → `page.context().cookies('https://elexikon.ch')`.
  - Screenshot fallback (`browser_take_screenshot {fullPage:true, scale:"device"}`) still works
    for a one-off spread, but downsamples to ~2366 px wide.
- **For exact signatures / fine print, crop and zoom** with `scripts/crop.py` (Pillow available).
  On the **native** PNG (3685×2592) the 4 columns are roughly **A: 0–921, B: 921–1842,
  C: 1842–2763, D: 2763–3685** (x px; y as 0–1 fractions). crop.py's docstring numbers assume
  the older ~3620-wide screenshot — scale to the actual image width.

## Making edits (through the browser session)

All writes go through the logged-in browser via the MediaWiki API in `browser_evaluate`
(same-origin cookies). Be on a `de.wikisource.org` page first. Pattern:

```js
async () => {
  const api = '/w/api.php';
  const title = 'RE:...';
  const tk = await (await fetch(`${api}?action=query&meta=tokens&format=json`, {credentials:'same-origin'})).json();
  const token = tk.query.tokens.csrftoken;
  const q = await (await fetch(`${api}?action=query&prop=revisions&rvprop=content|timestamp&rvslots=main&titles=${encodeURIComponent(title)}&format=json&formatversion=2`, {credentials:'same-origin'})).json();
  const rev = q.query.pages[0].revisions[0];
  const oldText = rev.slots.main.content;
  const newText = /* ...transform... */ oldText;
  const body = new URLSearchParams({
    action:'edit', title, text:newText, format:'json',
    summary:'…', token, basetimestamp: rev.timestamp, bot:'0', nocreate:'1'
  });
  return await (await fetch(api, {method:'POST', credentials:'same-origin', headers:{'Content-Type':'application/x-www-form-urlencoded'}, body})).json();
}
```

- Always pass `basetimestamp` (edit-conflict safety) and guard that the string you replace
  actually exists before editing (report a SKIP otherwise).
- Loop the pattern to batch-edit many titles in one `browser_evaluate` call.
- Note: Lua modules (Scribunto) must be saved via api.php too — the on-wiki CodeEditor
  overwrites the textarea otherwise. (Regular wikitext articles are fine either way.)

**Batch editing at scale (100+ edits in one `browser_evaluate`):**

- Compute the *intended changes* locally, then send a **compact payload** (title + new values
  only: new REAutor string, new Spalte fields, SORTIERUNG, move target) — not full article text.
  Inject it as **base64** to dodge quoting/escaping of Greek + `ß`/umlauts:
  `JSON.parse(new TextDecoder().decode(Uint8Array.from(atob(B64), c=>c.charCodeAt(0))))`.
- In the loop, **fetch each article's live text and apply targeted replacements** (regex-replace
  the single `{{REAutor|…}}`; line-replace `^\|SPALTE_END=.*$`; fill `^\|SORTIERUNG=\s*$`). This
  is robust to overnight ReScanner regeneration — if the guard (`exactly one REAutor tag`, line
  present, SORTIERUNG empty) fails, record a SKIP instead of clobbering. Only POST when the text
  actually changed; skip `NOCHANGE`.
- Pass `maxlag:'5'` and **pace ~700 ms** between edits ("THE IT" is not a bot account, so it hits
  manual rate limits). Collect a per-title `{status}` result array and save it via `filename:`.
- **Do moves in a second pass, after the text edits** (set `SORTIERUNG` in the text pass on the
  old title, then move). Same base64-inject + pacing pattern.

## REAutor = the EXACT printed signature

Set `{{REAutor|...}}` to the **verbatim** bracketed signature in the scan. Do **not** leave an
expanded/mapped form. Keep the trailing period as printed. Examples seen:

| Printed | Correct REAutor |
|---|---|
| `[Drachmann.]` | `Drachmann.` (not "A. G. Drachmann.") |
| `[W. Ruge.]` | `W. Ruge.` (not "Ruge.") |
| `[Eugen Oberhummer.]` | `Eugen Oberhummer.` (not "Oberhummer.") |
| `[Konrat Ziegler.]` | `Konrat Ziegler.` |
| `[F. Münzer.]` | `F. Münzer.` |

Replace with a regex on the single template: `oldText.replace(/\{\{REAutor\|[^}]*\}\}/, '{{REAutor|'+author+'}}')`.

## Greek headwords → move to the Greek lemma

RE lemmas are often stored as **Latin transliterations** while the printed headword is
**Greek** (so searching the scan for the Latin string finds nothing — recognize the Greek
form). Diacritics track the print exactly: `RE:Τρητόν` (acute, standalone) vs
`RE:Τρητὸν ἄκρον` (grave, before a following word). A bold Greek headword = move it; a Latin
headword with the Greek only in parentheses (e.g. `Trochilos (Τροχίλος)`) = **no** move.

**Move rule:** move the page to the **exact printed Greek headword, including any leading
article** (e.g. `ἡ Τροβαλισσικὴ ὁδός` → `RE:ἡ Τροβαλισσικὴ ὁδός`), leaving the transliteration
as a redirect. Then set `SORTIERUNG=<transliteration>` on the moved page for category sorting
(cf. `RE:Λεβήν` has `SORTIERUNG=Leben`). Leave the article-body bold headword as-is. Move +
redirect is sufficient — no register-data edit needed (the nightly ReScanner won't fight it).
Use `action=move` (csrf token, leave the redirect; check the target doesn't already exist).

- **Leaving the redirect — MediaWiki boolean gotcha:** `noredirect` is treated as *true* if the
  parameter is **present at all**, regardless of value — passing `noredirect:'0'` (or `'false'`,
  `''`) still **suppresses** the redirect. To keep the redirect, simply **omit `noredirect`
  entirely** from the move request.
- **Always verify after moving** that the old title now exists as a redirect (query its content).
  If it's missing, recreate it: `#WEITERLEITUNG [[RE:<greek>]]` + `[[Kategorie:RE:Redirect]]`
  (cf. `RE:Leben`).

## Nachtrag / band chains — Vorgänger/Nachfolger gotcha

RE pages can hold **multiple REDaten blocks**, one per band (main text e.g. `BAND=VII A,1`,
second half-band `VII A,2`, and the Register `BAND=R`). Cross-reference stubs printed
**"s. am Schluß des Bandes / Halbbandes"** are *Nachtrag* lemmas whose real content lives in
VII A,2 / R, and they form their **own** band-chain — separate from the main-text chain.
Example: Band-R chain `Troezene → Trogitis → Trogodytai → Troia 1 → Troiaspiel` runs alongside
the VII A,1 chain `… → Trogus → Troia 2 → …`. **Do not conflate them.**

- A break in Vorgänger/Nachfolger may just be two different band-chains — inspect each lemma's
  `BAND=` before concluding it's wrong.
- The nightly **ReScanner regenerates V/N from register data**, so hand-edits to these fields
  may be reverted overnight — mention this when you touch them, and prefer minimal edits.
- The other verweis kind — a plain `s. <article>` (e.g. `Troiae lusus` "s. Lusus",
  `VERWEIS=ON`) — *is* part of the main chain.

## Person articles

Articles about people (they carry `GEBURTSJAHR`/`TODESJAHR` fields) use the category variant
**`[[Kategorie:RE:Stammdaten überprüfen, Personen]]`** instead of the plain
`[[Kategorie:RE:Stammdaten überprüfen]]`. Handle both.

## Workflow & user preferences

- Work in batches the user tells you about. If no number is given, ask.
- **Parallelize the verification step across 10 subagents.** There is only **one** browser
  session and it's the only thing that can reach elexikon — so subagents **cannot** fetch scans
  themselves. Instead, the main session first **pre-downloads every needed scan to local PNG
  files** (see the at-scale download above) and bulk-fetches all wikitext, then fans out ~10
  subagents (roughly one per ~20 lemmas). Give each subagent a chunk of assignments — per
  article the local scan-file paths + a column→position (A/B/C/D) map + the wikitext path — and
  have it **only read local files + `crop.py`** (no browser, no web). Each writes a
  `findings_NN.json` (exists / spalte_fix / reautor_printed / greek_move+title / confidence).
  Collect all findings, then do the edits/moves sequentially through the single browser session.
- Per article, in one pass: verify Spalte/Vorgänger/Nachfolger → set **REAutor to the exact
  signature** → **move** to the Greek lemma if the headword is Greek → (only with the user's
  agreement) any Vorgänger/Nachfolger chain fix.
- **Do NOT remove the `RE:Stammdaten überprüfen` category.** The **user keeps the last check
  and removes the maintenance category themselves.** Leave it in place for their review.
- **Don't open the articles in browser tabs.** Instead hand over a **written report** — a
  Markdown table of every change (REAutor / Spalte / move, with the *moved* Greek titles where
  applicable), grouped by type, so the user can scan it and work the category page themselves.
  Note which entries are high-confidence signature expansions vs. the review-worthy ones
  (Greek moves, wrong-author fixes, Spalte changes).
- Never touch the `RE:Kurztext überprüfen` category.
- If an article is genuinely problematic, multi-part, or too complex, **skip it and ask** /
  optionally note it on the category talk page — don't guess.
- **Surface data-model surprises before editing** rather than guessing (e.g. multi-band pages,
  register-driven fields).
- do all editing with one edit, **do not split edits**.

## Helper

`scripts/crop.py <scan.png> <x0> <y0frac> <x1> <y1frac> <out.png> [scale]` — crop a region of a
saved scan (y as 0–1 fractions of height) and upscale, for reading fine print / signatures.

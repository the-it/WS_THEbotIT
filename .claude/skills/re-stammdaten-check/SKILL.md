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
3. **VORGÄNGER / NACHFOLGER** are really the articles printed before/after — **verify both
   explicitly against the scan, every time.** Obey the scan exactly: do **not** assume the
   preceding/following lemma is already correct just because it looks plausible or matches the
   register — read the actual neighbouring headwords on the spread (the lemma immediately before
   this article's start column, and the one immediately after its end column) and set VORGÄNGER
   /NACHFOLGER to what is genuinely printed. (Regression: at `RE:Tuficum` a neighbour was taken
   on trust instead of being checked against the scan, and it was wrong.) See the Nachtrag/band-
   chain gotcha below — but "don't over-eagerly fix" means *confirm with the scan first*, not
   *leave it unchecked*.
   - **When you touch an article at all, re-verify ALL of Spalte + V/N + REAutor in the same
     pass — don't tunnel-vision on the field you came to fix.** A wrong bot-generated V/N sitting
     next to a field you *are* correcting is easy to skip past. (Regression: at `RE:Tydeus 2` the
     REAutor and SPALTE_END were fixed from the scan, but the bot's `NACHFOLGER=Tylangii` was left
     unchecked — the scan shows Tydeus 2 `[Wolf Aly.]` is directly followed by `Tydii`
     `[Erich Diehl.]`, so the successor was `Tydii`.)
   - **The register V/N can be *scrambled*, not just off-by-one:** an alphabetically-later, longer
     article can be spliced into the middle of a run even though it is printed further on. At
     `RE:Tydeus 2` the register read `… → Tylangii → Tydii → Tyenis …`, but the print order is
     `Tydeus 2 → Tydii → Tyenis → Tylangii` (Tylangii, "Keltisches Volk im Wallis", actually
     begins at the bottom of col 1709 *after* Tyenis). Trust the on-scan headword/signature
     sequence, not the register order. A whole-run scramble is a multi-article chain fix — apply
     the whole chain (both outside neighbours included) once each link is verified on the scan;
     the user asked for scan-verified V/N fixes to be applied autonomously (2026-07-16). List
     them prominently in the report. V/N do **not** regenerate nightly, so hand-edits persist.
4. **REAutor** = the **exact** signature printed in `[ ... ]` at the article's end
   (see "REAutor" below). Short articles may share the *next* signed article's author; pure
   redirects/verweise get `{{REAutor|OFF}}`.
5. **HEADWORD = lemma name — read it character for character.** Read the *printed* bold headword
   (and the page running head) and confirm the page title matches it exactly — **case and
   punctuation included** — don't just check Spalte/author and move on. Five ways the
   auto-generated title is wrong: a **Greek** headword (see below), a **double lemma** (see
   "Double lemmas" below), **letter case** (see "Letter case" below), a **parenthetical
   reconstruction** (see "Parenthetical headwords" below), and a **reversed person-name** (see
   "Reversed person-name" below). Regressions: `RE:Turba 1/2/3` read "Turba 1) oder Turbula"
   (→ `RE:Turba, Turbula 1/2/3`); `RE:Turmuca` was printed lowercase **"turmuca"**; `RE:Turolici`
   was printed **"Turol(ici)"** with the reconstructed ending in parentheses; `RE:Val., P.` was
   printed **"P. Val."** (praenomen before nomen). All had correct Spalte/V/N/REAutor and were
   missed by not reading the headword.

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
  2. In a single `browser_evaluate`, loop the needed pages, `fetch()` each PNG **with
     `credentials:'include'`** (CRITICAL: `credentials:'omit'` drops the `cf_clearance` cookie
     and every fetch 403s — this looks exactly like a rate limit but is NOT; with the cookie
     included, ~30 files/batch at 700 ms pacing download 100% clean and there is no rate limit).
     base64-encode the `arrayBuffer` (chunk the `String.fromCharCode` in ~8 KB slices or big
     PNGs blow the call stack), and return them joined; save with the `filename:` param so
     the (multi-MB) blob lands in a file **instead of your context**. Early-stop a batch on
     ~3 consecutive 403s and re-solve the challenge rather than hammering (repeated 403s while
     blocked can invalidate `cf_clearance` and trigger a fresh "Just a moment…" challenge — just
     re-navigate + `browser_wait_for {time: 10}`). Then base64-decode
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
| `[Güngerich.]` | `Güngerich.` (not "Rudolf Güngerich") |

Replace with a regex on the single template: `oldText.replace(/\{\{REAutor\|[^}]*\}\}/, '{{REAutor|'+author+'}}')`.

**The most common REAutor error is over-expansion, and it hides in plain sight.** The bot fills
REAutor from its author database as a **full name with no trailing period** (e.g. the print
`[Güngerich.]` became `{{REAutor|Rudolf Güngerich}}`). Because that *looks* like a legitimate
author, it is easy to glance past and leave unchanged — but it is wrong twice over (expanded form
+ missing period). **Diff every REAutor against the exact printed signature in both directions**
(under-expanded bare surname *and* over-expanded full name), and treat a missing trailing period
as a diff. Do not assume an already-plausible full name is correct. (Regression: `RE:Tuscianus 1`
kept `Rudolf Güngerich` when the print reads `[Güngerich.]` — it was never re-checked against the
scan.)

**Do NOT overwrite these REAutor forms — they are deliberate author-template syntax, not raw
signatures (flag for the user instead):**
- **Band-disambiguation `Autor|Band`** (e.g. `{{REAutor|Nagl.|VII A,2}}`) — the `|VII A,2`
  param disambiguates an ambiguous surname (several "Nagl" authors); replacing it with the
  printed full name (`Assunta Nagl.`) breaks the disambiguation.
- **Maiden-name redirect `Vorname s. Mädchenname Ehename`** (e.g. `Dorothea s. Lunzer Sträussler`).
- **Dual-/multi-author articles**: one page whose sections carry *different* printed signatures
  (e.g. Tympanum: §1–5 `[K. Schneider.]`, §6–7 `[O. Reuther.]`). Don't clobber the first author
  with the last signature. Represent each author with its **own** `{{REAutor|<AUTHOR>.}}` at the
  end of that author's section, separated by **`{{REAbschnitt}}`**:
  ```
  …text of first author's sections…
  {{REAutor|K. Schneider.}}
  {{REAbschnitt}}
  …text of next author's sections…
  {{REAutor|O. Reuther.}}
  ```
  Each block closes with its `{{REAutor|…}}`; `{{REAbschnitt}}` goes *between* blocks; the last
  block has no trailing `{{REAbschnitt}}`. (Working example: `RE:Tullius 29` chains
  `Matthias Gelzer.` → `{{REAbschnitt}}` → `W. Kroll.` → `{{REAbschnitt}}` → `Philippson.|VII A,1`
  …) The single-`{{REAutor|…}}` guard/regex only handles the one-author case — for these, insert
  the extra `{{REAutor}}`+`{{REAbschnitt}}` instead of a blind replace.
- A guard of "exactly one `{{REAutor|…}}` tag" is right, but also skip when `cur` contains `|`
  or ` s. `. **Run the `|`/` s. ` test on the captured author *value* — the text between
  `REAutor|` and `}}` — not on the whole `{{REAutor|…}}` string**, or the template's own separator
  pipe false-positives and you skip every ordinary single-author article. Capture with
  `/\{\{REAutor\|([^}]*)\}\}/` and test group 1.

## Letter case matters → the lemma must match the printed case

The bot **auto-capitalizes** the first letter of a lemma, but some RE headwords are printed with
a **lowercase initial** — typically Etruscan/foreign inscription words or transliterations
(e.g. running head **"turmuca"**, an Etruscan word in the turmś/aitaś group). Whenever the printed
bold headword / running head starts lowercase (or has internal case the title doesn't), the
auto-generated title is wrong.

- **Compare the title's case to the print, every time** — this is easy to miss because Spalte, V/N
  and REAutor can all be right while only the case is wrong (that is how `RE:Turmuca` slipped
  through).
- **Fix by moving** `RE:Turmuca` → `RE:turmuca` (leave the redirect; omit `noredirect`).
  de.wikisource's RE namespace permits a lowercase first character even though MediaWiki normally
  capitalizes titles.
- Also lowercase the **body bold headword** to match (`'''Turmuca'''` → `'''turmuca'''`).
- This is a scan-verified, review-worthy change (like Greek/double-lemma moves) — list it in the
  report and check the exact case on the scan crop before moving.

## Reversed person-name ("Val., P." → "P. Val.") → restore the printed word order

For a person lemma whose printed headword is an abbreviated **praenomen + nomen** (e.g. bold
**"P. Val.,"** = P. Valerius, *praeses provinciae Sardiniae*), the bot sometimes stores the
**sort form** — *nomen, praenomen* — as the title and body headword: `RE:Val., P.` with
`SORTIERUNG=Val.,p.`. The printed lemma is the natural order **"P. Val."**, so the title is wrong.

- **Fix by moving** `RE:Val., P.` → `RE:P. Val.` (leave the redirect) and set the body bold
  headword to the printed order `'''P. Val.'''`.
- The `SORTIERUNG` (`Val.,p.`) is the reversed *sort* key and is fine to keep — it correctly files
  the entry under the gens (Valerius), which is why the bot generated the reversed **title** in
  the first place. Don't confuse the two: sort key reversed = OK; **title reversed = wrong**.
- Update the two chain neighbours that point at the old title (here the real neighbours were the
  Greek lemmas `RE:Οὐακουᾶται` / `RE:Οὔαλα 1`, since `Uakuatai`/`Uala` are themselves redirects).
- Scan-verified, review-worthy — list it in the report.

## Parenthetical headwords (reconstruction: "Turol(ici)", "Theba(i)genes") → keep the parens

Some RE headwords print **parentheses inside the word** to mark an editorially **reconstructed /
supplemented** part — usually because the attested source (an inscription) only preserves a
fragment. The auto-generated lemma silently drops the parens (expands to the full form), which is
**wrong**: the lemma must reproduce the parentheses verbatim. Distinguish this from a double lemma
`X (Y)` (two whole alternative words, comma form) — here the parens sit **inside one word**:
`Turol(ici)`, `Theba(i)genes`, `Turoni (Turones)`.

- Example: `RE:Turolici` → **`RE:Turol(ici)`**. Reason (read it off the scan): the inscription
  CIL II 431 reads only *"Larib. Turol. consecr."*, so `Turol` is attested and `ici` is the
  editor's completion → RE prints `Turol(ici)`. The bold body headword is `'''Turol(ici)'''`.
- **Fix by moving** `RE:<expanded>` → `RE:<with parens>` (leave the redirect — the paren-less
  expanded form is a useful search redirect and the move creates it automatically). Then fix the
  body bold headword to the paren form.
- `SORTIERUNG` stays **empty** and **no extra redirect** is needed (matches the `RE:Theba(i)genes`
  precedent, whose paren-less forms don't exist as redirects).
- Update the V/N of the two neighbours pointing into the article to the paren form.
- Scan-verified, review-worthy change — list it in the report.

## Double lemmas (Doppellemma: "X oder Y" / "X (Y)") → move to the comma form

RE often prints a headword with a **byform**: the running head reads `X (Y)` and the article
body opens `'''X 1)''' oder '''Y.'''` (e.g. running head "Turba (Turbula)", body "Turba 1) oder
Turbula"). The auto-generated lemma keeps only the primary word (`RE:Turba 1`), which is **wrong**
— the RE-Werkstatt convention titles such articles with the **comma form** `RE:X, Y N`, and it
applies to **every numbered sub-article** of that headword, not just Nr. 1 (confirmed by e.g.
`RE:Aqua, Aquae 55`, `RE:Agreus, Agreutes 1/2`, `RE:Castra, Castrum 33`, `RE:Ilion, Ilios 1`).
Detect it by **reading the printed headword and running head** — Spalte/V/N/REAutor can all be
correct while the title is still wrong (that is exactly how `RE:Turba` was missed).

- **Verify the byform against the scan** (the "oder Y" / "(Y)" in the print), then **move**
  `RE:X N` → `RE:X, Y N` for each N in the group, **leaving the redirect** (omit `noredirect`).
- Only Nr. 1's body repeats the full bold double headword — fix it to `'''X 1)''' oder '''Y.'''`
  (match the print). Nr. 2, 3, … keep their bare `'''2)'''` body.
- **Fix the whole V/N chain to the new titles**: each moved article's VORGÄNGER/NACHFOLGER, plus
  the two outside neighbours (the article before Nr. 1 and after the last N) that point *into*
  the group. The old-title redirects keep links working, but update them for a clean chain.
- `SORTIERUNG` can stay empty — `X, Y` already sorts under `X`. No SORTIERUNG needed (unlike Greek
  moves).
- **Register caveat:** the nightly ReScanner regenerates the **lemma name** from the on-wiki RE
  register. If the register still holds the single name (`Turba`), the move may be regenerated
  back to `RE:X N` overnight. Flag this to the user — the durable fix is in the register data, not
  just the on-wiki move. (This applies to the lemma name/title only — **V/N do not regenerate
  nightly**, so V/N hand-edits are durable.)

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
Then update the two neighbours whose V/N still hold the old transliteration to the new Greek
title (the redirect keeps them working, but the chain should carry the real lemma — the
Uellegeia move left `Velleboroi.N`/`Velleia.V` on the old name until follow-up, 2026-07-16).

- **Transcribe the Greek letter by letter from a zoomed crop — a misspelled Greek move is a real
  error another editor has to clean up.** Do **not** type the word from memory or approximate it;
  `crop.py` the headword and read every letter/accent/breathing. Two specific traps:
  - **The lemma is the FIRST bold headword.** What follows `v. l.` (*varia lectio*) are **variant
    readings, not the title** — do not move to a v.l. form, and do not blend the main form with a
    variant.
  - **Don't insert phantom letters.** (Regression: `RE:Tukrumuda`'s headword is
    **`Τουκρούμουδα`** (…μουδα), with v.l. `Τουκρούμονδα`/`Τουρκούμουδα`; the move went to
    `Τουκρούμου`**ν**`δα` — a spurious `ν` blended in from the variant, matching neither form, and
    editor *Epìdosis* had to re-move it to the correct `Τουκρούμουδα`.)
  - After moving, re-read the moved title against the crop once more to confirm the spelling.

- **Leaving the redirect — MediaWiki boolean gotcha:** `noredirect` is treated as *true* if the
  parameter is **present at all**, regardless of value — passing `noredirect:'0'` (or `'false'`,
  `''`) still **suppresses** the redirect. To keep the redirect, simply **omit `noredirect`
  entirely** from the move request.
- **Always verify after moving** that the old title now exists as a redirect (query its content).
  If it's missing, recreate it: `#WEITERLEITUNG [[RE:<greek>]]` + `[[Kategorie:RE:Redirect]]`
  (cf. `RE:Leben`).

## Nachtrag / band chains — Vorgänger/Nachfolger gotcha

RE pages can hold **multiple REDaten blocks**, one per band (main text e.g. `BAND=VII A,1`,
second half-band `VII A,2`, and the Register `BAND=R`).

**EVERY printed cross-reference stub is part of the band's V/N chain.** V/N = the lemma
printed immediately before/after, no exceptions: plain `s. <article>` verweise, `s. d. Suppl.`
stubs, AND `s. am Ende/Schluß des Bandes` Nachtrag stubs all count. If the register skips a
printed stub, that's a register error — fix the chain to the printed sequence (both
neighbours; the stub's own same-band block too, if the page exists). Do NOT read the
existence of other-band chains as "the main chain skips the stub". (Regression, batch
2026-07-16: `Veltae→Veltinia tribus→Velvinus` was chained past the printed
`Weltalter/Weltbild/Weltschöpfung/Weltwunder` stubs, likewise `Venasa`, `Veneris oppidum 3`
and `Uennikioi`/`Uennikion akron` were skipped — the user had to correct it. The register is
inconsistent about stubs, so its current value is no evidence either way.)

Where the **separate band-chain** point actually applies: the stub's *page* usually holds
additional REDaten blocks for the band where the content really lives (VII A,2 Nachtrag,
`BAND=R` Register, Supplement bands). Those blocks chain within *their* band (e.g. Band-R
`Troezene → Trogitis → Trogodytai → Troia 1 → Troiaspiel` alongside the VII A,1
`… → Trogus → Troia 2 → …`) — leave them alone, and:

- A seeming break in Vorgänger/Nachfolger may just be another band's block — inspect each
  block's `BAND=` before concluding it's wrong.
- **V/N do NOT regenerate nightly** — hand-edits to VORGÄNGER/NACHFOLGER are durable and are
  **not** reverted overnight. (Don't tell the user a V/N fix "will regenerate" — that's wrong.)
- **Two adjacent stubs can be SWAPPED in the register** (batch 2026-07-17: print order
  `Vercingetorix → Verconnius Herennianus → Vercondaridubnus → Vercustis`, register had the
  two stubs reversed). The stubs' own pages exist as Verweis pages with their own V/N — fetch
  and fix those too, not just the batch article pointing at them.
- **After every move, sweep for ALL pages whose V/N hold the old lemma**: batch-internal via
  a rename map over `all_meta.json`, plus the outside neighbours (derive them from the moved
  article's own corrected V/N and fetch them — batch 2026-07-17 needed 7 such outside edits,
  e.g. `Fundus Ver...`→`ver sacrum`, `Verrucini`→`C. Verrucius`, `Verbalis`→`Verban(n)us lacus`).
  Also check whether the move TARGET already exists first — neighbours may already point at the
  correct (e.g. Greek) lemma even though the page itself is still at the transliteration.
- **A printed signature that looks like a misprint still wins** (Sp. 968 prints
  `[E. A. Gordon.]` though the author was Arthur E. Gordon = "A. E."): set REAutor to the
  printed form, verify on a crop yourself, and flag it prominently in the report.

## Person articles

Articles about people (they carry `GEBURTSJAHR`/`TODESJAHR` fields) use the category variant
**`[[Kategorie:RE:Stammdaten überprüfen, Personen]]`** instead of the plain
`[[Kategorie:RE:Stammdaten überprüfen]]`. Handle both — the PetScan worklist and the fan-out
**must include the Personen variant**, and every lemma needs a findings entry (re-spawn missing
chunks). A person article is especially prone to the over-expanded REAutor above, because the
author DB expands the surname to the full name. (Regression: `RE:Tuscianus 1`, a Personen article,
was left entirely untouched — only the bot's `Automatisch generiert` revision existed — so its
`Rudolf Güngerich` / `[Güngerich.]` mismatch was never caught. If the maintenance category is
still present and there is no `THE IT` revision, the article was never processed: check it.)

## Workflow & user preferences

- Work in batches the user tells you about. If no number is given, ask.
- **Parallelize the verification step across 5 subagents.** There is only **one** browser
  session and it's the only thing that can reach elexikon — so subagents **cannot** fetch scans
  themselves. Instead, the main session first **pre-downloads every needed scan to local PNG
  files** (see the at-scale download above) and bulk-fetches all wikitext, then fans out ~10
  subagents (roughly one per ~20 lemmas). Give each subagent a chunk of assignments — per
  article the local scan-file paths + a column→position (A/B/C/D) map + the wikitext path — and
  have it **only read local files + `crop.py`** (no browser, no web). Each writes a
  `findings_NN.json` (exists / spalte_fix / reautor_printed / greek_move+title / confidence).
  Collect all findings, then do the edits/moves sequentially through the single browser session.
  - **Only the START and END spread matter per article** (start = exists/headword/VORGÄNGER;
    end = SPALTE_END/NACHFOLGER/signature) — you do NOT need the middle spreads of a long
    article. Trim each article's scan list to `{scan_page(SS), scan_page(SE)}` and chunk by a
    **scan-union budget (~12 spreads/subagent)**, not a fixed article count, so one long article
    (e.g. 22 spreads) doesn't bloat a subagent. This keeps each subagent light.
  - Subagents die on transient API errors ("Connection closed mid-response" / "ConnectionRefused")
    — findings files are the source of truth, so just re-spawn any chunk whose `findings_NN.json`
    is missing (idempotent; last writer wins). Verify page-move accents/numbering yourself via
    `crop.py` before applying — moves are hard to reverse and the subagents flag these as med.
- Per article, in one pass: verify Spalte/Vorgänger/Nachfolger → set **REAutor to the exact
  signature** → **move** to the Greek lemma if the headword is Greek → apply any
  Vorgänger/Nachfolger chain fix (scan-verify every link yourself first — crop the spot for
  each medium-confidence reading; the user asked for these to be applied autonomously,
  2026-07-16). Remember: printed stubs belong in the chain (see the Nachtrag section).
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

## Helpers (`scripts/`) — prefer these over re-writing one-off Python each run

All take the batch **work dir** (`<outdir>`, e.g. `.claude_work_dir/assign`) and/or the
**scans dir** (default `.claude_work_dir/scans`). Run them with literal paths (no shell
expansion). The whole pipeline, in order:

1. `scripts/fetch_wikitext.py <petscan.json> <outdir> [--email you@…]` — bulk-fetch every
   article's wikitext via the query API (50/POST, descriptive UA) and extract Stammdaten →
   `<outdir>/all_wikitext.json` + `all_meta.json`. Also accepts a plain one-title-per-line `.txt`.
2. `scripts/scan_pages.py <outdir>` — print the scan-page union (start+end spread per article)
   grouped by BAND, with the exact `<prefix>_<page>.png` filenames to download. (`--cols 42 116`
   for an ad-hoc lookup.) Download those spreads in the browser (see "Getting the scans").
3. `scripts/decode_scans.py <b64_batch.json> <scansdir> <BANDPREFIX>` — turn the in-browser
   base64 batch (the evaluate `filename:` output) into verified PNGs
   `<scansdir>/<BANDPREFIX>_<page>.png` (e.g. prefix `VIIIA,1`).
4. `scripts/build_chunks.py <outdir> [num_chunks=10] [scansdir]` — split into
   `<outdir>/chunk_NN.json`, each article carrying wikitext + start/end scan file paths + column
   A/B/C/D positions, for the offline subagent fan-out.
5. `scripts/aggregate_findings.py <outdir>` — merge the subagents' `findings_*.json` →
   `<outdir>/all_findings.json` and print grouped counts (REAutor / SPALTE / V/N / moves /
   low-med) to drive the apply-vs-hold decision.
6. `scripts/crop.py <scan.png> <x0> <y0frac> <x1> <y1frac> <out.png> [scale]` — crop a region of
   a saved scan (y as 0–1 fractions of height) and upscale, for reading fine print / signatures.

The edit pass itself (REAutor/SPALTE regex-replace, V/N re-link) runs in the browser via
`browser_evaluate` (see "Making edits") — not a local script, because it needs the same-origin
login session.

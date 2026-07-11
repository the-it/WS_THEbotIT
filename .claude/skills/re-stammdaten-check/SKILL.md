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
  (`browser_navigate`, `browser_take_screenshot`, `browser_evaluate`, `browser_tabs`,
  `browser_wait_for`, `browser_snapshot`).

## What to verify against the scan (per article)

1. **Exists** at that RE issue (BAND + column).
2. **SPALTE_START / SPALTE_END** correct. `SPALTE_END=OFF` means single column (start == end).
   For multi-column articles, find the end by browsing the scans.
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

## Getting the scans (elexikon.ch)

- **elexikon.ch IS behind Cloudflare** — plain curl returns a "Just a moment…" challenge
  page. You **must** load scans in the Playwright browser. The `cf_clearance` cookie persists
  for a while but expires; if a navigation returns HTTP 403 / title "Just a moment…", call
  `browser_wait_for {time: 6}` and re-screenshot.
- **Don't guess the scan filename.** Get it from the article's rendered page:

  ```bash
  curl -s ".../w/api.php?action=parse&page=<urlenc>&prop=externallinks&format=json" \
    | python3 -c "import sys,json; d=json.load(sys.stdin); [print(u) for u in d['parse']['externallinks'] if u.endswith('.png')]"
  ```

  The `…VIIA,1_NNN.png` links are the scans (the "Bildergalerie im Original"). A multi-column
  article lists several.
- **One PNG = a 4-column two-page spread.** E.g. `VIIA,1_525.png` shows columns **523–526**;
  `_585.png` shows 583–586; spreads step by 4 (…_585, _589, _593, _597, _601…). So a handful
  of scans cover a whole batch — dedupe the scan list and read each spread once.
- **Read it:** `browser_take_screenshot {fullPage:true, scale:"device", filename:"scan_NNN.png"}`,
  then `Read` the saved PNG (it lands in the repo working dir). The full spread is legible for
  headwords/structure.
- **For exact signatures / fine print, crop and zoom** with the helper (Pillow is available):
  `scripts/crop.py` (see below). The saved screenshot is ~3620×3038; left page ≈ x 0–1780
  (col A ≈ 0–880, col B ≈ 880–1780), right page ≈ x 1840–3620 (col C ≈ 1840–2720,
  col D ≈ 2720–3620).

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

- Work in **batches of ~10**, pause after each.
- Per article, in one pass: verify Spalte/Vorgänger/Nachfolger → set **REAutor to the exact
  signature** → **move** to the Greek lemma if the headword is Greek → (only with the user's
  agreement) any Vorgänger/Nachfolger chain fix.
- **Do NOT remove the `RE:Stammdaten überprüfen` category.** The **user keeps the last check
  and removes the maintenance category themselves.** Leave it in place and **present the batch
  in browser tabs** (`browser_tabs` action:"new" per article, using the *moved* Greek titles
  where applicable) for their review.
- Never touch the `RE:Kurztext überprüfen` category.
- If an article is genuinely problematic, multi-part, or too complex, **skip it and ask** /
  optionally note it on the category talk page — don't guess.
- **Surface data-model surprises before editing** rather than guessing (e.g. multi-band pages,
  register-driven fields).
- do all editing with one edit, **do not split edits**.

## Helper

`scripts/crop.py <scan.png> <x0> <y0frac> <x1> <y1frac> <out.png> [scale]` — crop a region of a
saved scan (y as 0–1 fractions of height) and upscale, for reading fine print / signatures.

---
name: re-split-series-intro
description: >-
  Split out the introductory "zum Namen" lemma for a series of same-name RE (Pauly
  Realencyclopädie) articles on de.wikisource and insert it into the Vorgänger/Nachfolger
  chain. Creates a new RE:<Name> header lemma (placeholder body, KURZTEXT=zum Namen) with
  scan-verified Stammdaten, then relinks the two neighbours so the chain reads
  … → <predecessor> → <Name> → <Name> 1 → …. Use when the user wants to create / split out
  the name-introduction (Namensartikel / "zum Namen") in front of RE:<Name> 1, <Name> 2, …
  or to insert a missing header article into an RE article chain.
---

# RE — Split out the series introduction ("zum Namen")

An RE name-series (`RE:Tuccius 1`, `RE:Tuccius 2`, …) is printed under a general **name
header** — a short "zum Namen" note about the gens/name that precedes the numbered entry `1)`.
On de.wikisource that header often has **no lemma of its own**; instead the first numbered
article `RE:<Name> 1` is chained directly after whatever preceded the series. This skill
**creates the missing intro lemma `RE:<Name>`** (placeholder body, scan-verified Stammdaten)
and **inserts it into the Vorgänger/Nachfolger chain** in front of `RE:<Name> 1`.

Worked example (what "done" looks like), the *Tuccius* case:

```
before:  … → Tuccianus 2 ─────────────→ Tuccius 1 → Tuccius 2 → …
after:   … → Tuccianus 2 → Tuccius → Tuccius 1 → Tuccius 2 → …
                             ▲ new intro lemma (KURZTEXT=zum Namen)
```

## Shared machinery — reuse `re-stammdaten-check`

This skill runs on the **same infrastructure** as the `re-stammdaten-check` skill. Do **not**
re-derive it; read that SKILL.md for the details and reuse:

- **Edits:** all writes run as the bot account **THEbotIT** via **pywikibot** — see the
  stammdaten skill's "Making edits (pywikibot as THEbotIT)" for the pattern (OAuth in
  `~/.pywikibot/user-config.py`, repo venv interpreter, script + JSON payload in
  `.claude_work_dir`). No wikisource browser login is needed; Playwright (MCP tools are
  deferred — load with ToolSearch) is only for the elexikon scans.
- **Reading wikitext:** de.wikisource is not behind Cloudflare — plain
  `curl ".../index.php?title=<t>&action=raw"` (with a descriptive `User-Agent`) works for a
  few pages; bulk-fetch via the query API otherwise.
- **Scans (Stammdaten verification):** elexikon.ch **is** behind Cloudflare — load scans in the
  Playwright browser. Compute the filename from `BAND`+column (`scan_page(col)`), and use
  `../re-stammdaten-check/scripts/crop.py` to zoom in on the printed signature.
- **REAutor rule, Greek-headword move rule, Nachtrag/band-chain gotcha** — all apply here too.

## Step 1 — Identify the series and the insertion gap

1. The series is `RE:<Name> 1`, `RE:<Name> 2`, …. The **first numbered article** is
   `RE:<Name> 1`.
2. Read `RE:<Name> 1`'s current `VORGÄNGER` — call it **P** (the article printed before the
   series, e.g. `Tuccianus 2`). Confirm `P`'s current `NACHFOLGER` is `<Name> 1` (the chain you
   are about to splice into). If they don't match, **stop and surface it** — a mismatch usually
   means a band-chain split (see the Nachtrag gotcha) and must be resolved first.
3. Check whether `RE:<Name>` **already exists**:
   - Missing → you'll create it in Step 3.
   - A **redirect** to `RE:<Name> 1` (common — the bare name often redirects to entry 1) →
     you'll **overwrite the redirect** with the intro article in Step 3.
   - A **real article** already → stop and ask; the intro may already exist under a different
     form.

## Step 2 — Verify the intro's Stammdaten against the scan

Determine these from the **printed scan** (not by blindly copying entry 1):

- **BAND** — the intro's own band (usually the same as `<Name> 1`; a page can mix bands, so
  read it).
- **SPALTE_START** — the column where the **name header** begins. This can be an **earlier
  column** than where `1)` starts, because the general note is printed above the first entry.
  Read the scan; don't assume `<Name> 1`'s start.
- **SPALTE_END** — `OFF` if the intro sits in a single column (start == end); otherwise the
  column holding its last line (apply the `re-stammdaten-check` SPALTE_END rule).
- **REAutor** — the **exact printed signature** governing the name note. The "zum Namen" note
  is frequently **unsigned** and shares the signature of the following entry (per the "short
  articles share the next signed author" rule) — verify on the scan which `[ … ]` applies.
- **Greek headword?** If the name is a Greek word printed in Greek, the intro lemma belongs at
  the **Greek title** — create `RE:<Greek>` and set `SORTIERUNG=<transliteration>` (apply the
  `re-stammdaten-check` Greek-move rule).

Surface the verified values to the user before writing.

## Step 3 — Create the intro lemma `RE:<Name>`

Create it via pywikibot (`pywikibot.Page(site, 'RE:<Name>')`, set `page.text`,
`page.save(summary=…)` — creating the page or overwriting a redirect is fine here; this
is the one write in these skills that intends creation). Body is a **placeholder stub** —
the user fills the real intro text later.

```wikitext
{{REDaten
|BAND=<verified band>
|SPALTE_START=<verified start>
|SPALTE_END=OFF
|VORGÄNGER=<P>
|NACHFOLGER=<Name> 1
|SORTIERUNG=<transliteration, only if Greek title; else empty>
|KORREKTURSTAND=unvollständig
|KURZTEXT=zum Namen
|WIKIPEDIA=
|WIKISOURCE=
|GND=
|KEINE_SCHÖPFUNGSHÖHE=OFF
|TODESJAHR=
|GEBURTSJAHR=
|NACHTRAG=OFF
|ÜBERSCHRIFT=OFF
|VERWEIS=OFF
}}
'''<Name>.''' 
[...]
{{REAutor|<exact signature>.}}
[[Kategorie:RE:Kurztext überprüfen]]
```

- The intro is a **name note, not a person** — leave `GEBURTSJAHR`/`TODESJAHR` empty (no
  `RE:Stammdaten überprüfen, Personen`).
- Header is the **bare bold name** (`'''<Name>.'''`), no `1)`. Body `[...]` is a deliberate
  placeholder; `KORREKTURSTAND=unvollständig` + `RE:Kurztext überprüfen` mark it for later.
- Summary e.g. `Namensartikel angelegt / aus der Serie herausgelöst`.

## Step 4 — Relink the two neighbours

Two targeted, edit-conflict-safe edits (guard that the exact old string exists first):

1. **Predecessor `RE:<P>`** — `NACHFOLGER`: `<Name> 1` → `<Name>`.
   Line-replace `^\|NACHFOLGER=<Name> 1\s*$` → `|NACHFOLGER=<Name>`.
2. **First article `RE:<Name> 1`** — `VORGÄNGER`: `<P>` → `<Name>`.
   Line-replace `^\|VORGÄNGER=<P>\s*$` → `|VORGÄNGER=<Name>`.

**Do NOT remove `RE:Stammdaten überprüfen` (or the `, Personen` variant) from the neighbours.**
The user keeps the final Stammdaten check and removes the maintenance category themselves —
touch **only** the Vorgänger/Nachfolger field.

> Note: the nightly ReScanner regenerates Vorgänger/Nachfolger from register data, so these
> two field edits (and the new lemma's position) may need the register data updated too, or
> can be reverted overnight. Mention this to the user; keep the edits minimal.

## Step 5 — Verify and report

After the three writes, re-read all four lemmas and confirm the chain is consistent:

```
<P>.NACHFOLGER      == <Name>
<Name>.VORGÄNGER    == <P>
<Name>.NACHFOLGER   == <Name> 1
<Name> 1.VORGÄNGER  == <Name>
```

Also confirm `RE:<Name>` renders (no template error) and, if Greek, that the old title is a
redirect. Then hand the user a short written report — the new lemma's verified Stammdaten and
the two chain edits — so they can fill the intro text and do the final Stammdaten sign-off.

## Gotchas

- **Chain mismatch = band split, not a bug to force.** If `P.NACHFOLGER ≠ <Name> 1`, inspect
  each lemma's `BAND=` (Nachtrag / Register chains run separately) before editing — don't
  splice across two different band-chains.
- **The bare name may already redirect to entry 1** — overwrite that redirect with the intro
  article; don't create a second page or leave a self-redirect.
- **SPALTE_START is the header's column, not entry 1's** — verify on the scan; the general note
  can begin one column earlier.
- **One edit per page, `basetimestamp` on every write, guard-then-edit** — if the string to
  replace isn't present, report a SKIP instead of clobbering (same discipline as
  `re-stammdaten-check`).

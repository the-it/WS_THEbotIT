---
name: re-stammbaum
description: >-
  Reproduce a printed genealogical Stammtafel/Stammbaum from an RE (Pauly Realencyclopädie)
  article on de.wikisource with Vorlage:Stammbaum — decide which article the tree belongs to,
  pick the placement that mirrors the print, write the {{Stammbaum}} rows and connectors, and
  handle the expected check_assembly.py failure a plate {{Seite}} line causes. Use whenever an
  RE article's scan or OCR text shows a genealogical stemma/family tree, when filling or
  correcting such an article, or when the user asks for a Stammbaum/Stammtafel in RE.
---

# RE Stammtafeln — render a printed stemma with `Vorlage:Stammbaum`

Prosopographical RE articles (Roman gentes, Greek dynasties) frequently print a genealogical
stemma as a typeset tree. **A stemma is not a reason to skip an article** — reproduce it with
`Vorlage:Stammbaum`, which renders such a tree as an HTML table.

Roughly 34 RE articles already use it. `Vorlage:Stammbaum/Doku` is the syntax reference;
`RE:Acilius 20`, `RE:Antistius 48`, `RE:Annius 49`, `RE:Anicius 22ff.`, `RE:Aemilius 73` and
`RE:Arrius 39` are the house-style models cited throughout. Fetch any of them with
`…?action=raw` when you need a template to copy from — that is also how you get the two
non-ASCII glyphs right (see "Connectors").

## Step 0 — whose tree is it? (the Makartatos check)

Bad auto-OCR splices a **page-wide table into whichever article precedes it**, so the article
you are filling may carry a stemma that belongs to its *neighbour*. `RE:Makartatos 1` was
exactly this: the Stammtafel in its text is printed under `RE:Makartatos 2`. Resolve ownership
before writing a single row:

1. On the **column scan**, find which printed headword the tree sits under, and which
   article's text runs into it above and continues below it.
2. Read the surrounding articles' bodies for a pointer at the tree — RE almost always has one
   (`Stammbaum s. auf S. 2559f. unten`, `*) Stammbaum der Acilii Aviolae Nr. 20ff.`, `Wir
   haben diese … Verwandtschaftsverhältnisse … in dem Stammbaum S. 2201/2 dargestellt`).
   The article that *points at* the tree owns it.
3. Check the **neighbour's wikitext** (`…action=raw`): if it already carries the tree, do not
   duplicate it — drop it from this article and note it in the report.

If ownership stays ambiguous after the scan, skip & report rather than guess.

## Placement mirrors the print

Four printed situations, four renderings — pick the one the scan shows:

1. **Tree at the end of the article, inside its own columns** → a `== Stammbaum ==` section
   after the body and **before** `{{REAutor|…}}` (`RE:Acilius 20`). If the print marks the
   tree with a `*)`-footnote, keep that as `<ref group="RE">…</ref>` in the body and put
   `<references group="RE" />` directly under the heading; `{{References|LIN|RE}}` at the end
   of the body is the equivalent (`RE:Antistius 48`).
2. **The print footnotes the whole tree** → put the tree *inside* the `<ref>…</ref>`
   (`RE:Arrius 39`: `<ref>Der Stammbaum ist folgender (vgl. …): {{Stammbaum/start}} … </ref>`).
3. **Tree printed on a later column of the volume, outside `SPALTE_END`** → its own
   `{{Seite|…}}` line plus a lead-in, e.g.
   `:(Zu S. 2268, 54.) Der {{Anker2|Stammbaum}} ist etwa folgender:` (`RE:Annius 49`) or
   `{{Anker|Stammbaum}}{{Seite|…}}` (`RE:Antistius 48`). The body then references it with
   `<ref>Stammbaum s. auf [[#Seite 2269–2270|S. 2269f. unten]].</ref>` — the anchor is the one
   the `{{Seite}}` line creates, so the page number in the link and in the `{{Seite}}` line
   must match byte for byte.
4. **Full-width plate spanning both printed columns** → open a `== Stammtafel ==` section
   (`RE:Anicius 22ff.`, which also carries its own plate `{{Seite}}` line as in case 3). If —
   and only if — the page already opened a BlockSatz, break the justified two-column layout
   first with `{{BlockSatzEnd}}{{BlockSatzStart||0|0}}` on its own line before the heading.
   Grep the article for `{{BlockSatzStart` before adding it: `{{REEL}}`-marker articles often
   have none, and an unmatched `{{BlockSatzEnd}}` is a stray template.

**Plate `{{Seite}}` lines take a Commons file name, not `{{REIA}}`/`{{REEL}}`** —
`{{Seite|2201–2202||Pauly-Wissowa I,2, 2201a - family tree Anicii.jpg}}`. Those files exist
because a human uploaded them. **Never construct such a name.** Verify it first
(`https://commons.wikimedia.org/w/api.php?action=query&prop=imageinfo&titles=File:<name>&format=json`);
if no plate scan is uploaded, use the bare `{{Seite|N}}` form and say so in the report — an
invented file name redlinks silently.

## Row syntax

Wrap every tree in `{{Stammbaum/start}}` … `{{Stammbaum/end}}`. A row is a list of cells;
cells that are letter placeholders get their content from same-named parameters at the end of
the same row:

```
{{Stammbaum/start}}
{{Stammbaum | | | | GRM |~|y|~| GRP | | GRM=Großmutter|GRP=Großvater}}
{{Stammbaum | | | | | | | |)|-|-|-|.| | }}
{{Stammbaum | | | MOM |y| DAD | | DAI | MOM=Mutti|DAD=Papa|DAI=Tante Wilma}}
{{Stammbaum | |,|-|-|-|+|-|-|-|.| | | | }}
{{Stammbaum | JOE | | ME  | | SIS | | | JOE=Mein Bruder Tim|ME='''Ich!'''|SIS=Meine kleine Schwester}}
{{Stammbaum/end}}
```

- Each box occupies **3 table columns**; the table is capped at **40 columns** (≈13 boxes
  wide). For anything wider use `{{Stammbaum (komplex)}}`.
- There must be **at least one `|` between two boxes** (two reads better and leaves room for
  the connector lines), and **a `|` before the parameter definitions**.
- **Name placeholders with 2–3 letters** (`GRM`, `DAD`, `AT`, `CA`), not one. A single letter
  that is also a connector code (`F 7 L J A V C D y Y v` …) is ambiguous — the Doku explicitly
  excludes those as box names. Longer than three characters hurts readability of the source.
- Per-row options come first: `border=0` (the RE articles use it throughout), `boxstyle=<css>`
  (e.g. `boxstyle=text-align:left`). Whole-table styling: `{{Stammbaum/start|style=…}}`.
- Box content may hold arbitrary wiki syntax: `<br>` for multi-line boxes, italics, and RE
  cross-links in either spelling — `[[RE:Antistius 46|'''46.''' C. Antistius Vetus]]` or
  `{{RE siehe|Anicius 22|'''22.''' Sex. Cocceius Anicius Faustus Paulinus}}`. Convention: the
  RE entry number is **bolded and followed by a full stop** inside the box.

## Connectors

All connector glyphs are plain ASCII — no Unicode traps:

- **solid:** `,` `.` `` ` `` `'` `^` `v` `(` `)` `-` `!` `+` and space
- **dashed:** `F` `7` `L` `J` `A` `V` `C` `D` `~` `:` `%`
- **mixed:** `é` `è` `<` `>` `*` `#` `y` `Y`

`y` is the **union (marriage) junction**; by convention the descent lines from mother and
father up to the union are drawn **dashed** (`GRM |~|y|~| GRP`). Inside box *text* only two
non-ASCII characters occur — `∾` (U+223E INVERTED LAZY S, "married to") and `†` (U+2020,
"died"). **Copy both out of an existing article rather than typing them.**

## `check_assembly.py` behaviour (verified on fixtures)

When the tree goes into an article the `create-ocr` skill is assembling, its structural check
(`.claude/skills/create-ocr/scripts/check_assembly.py`) still runs. The trigger for a failure
is **not** the placement case — it is whether the tree introduces a `{{Seite}}` line the
skeleton does not have. Cases 3 and 4 both typically do; cases 1 and 2 do not.

- A tree that adds **no** new `{{Seite}}` line **PASSes clean** — `== Stammbaum ==` /
  `== Stammtafel ==` headings are fine (only `== RE:` is rejected), and the body-length check
  only WARNs on *short* bodies, so a tree never trips it.
- A tree that adds a **plate `{{Seite}}` line** produces exactly one expected FAIL:
  `FAIL  no extra {{Seite templates: 2 in new vs 1 in skeleton`. Every other check still
  passes. Do **not** weaken the checker: confirm by eye that (a) the only extra `{{Seite}}`
  line is the plate line and (b) all the skeleton's own `{{Seite}}` lines survive
  byte-identically and in order — the run prints both — then proceed and record the override
  in the report.

## Inside a `create-ocr` fan-out

`create-ocr` fans articles out to offline `ocr-proofreader` subagents, which cannot check the
neighbouring article's wikitext or a Commons plate file — the two things Step 0 and the plate
`{{Seite}}` decision depend on. So **Stammtafeln stay with the main loop**. Brief subagents:
if the column text or scan shows a genealogical tree, transcribe the surrounding prose
normally, leave the tree out of `<lemma>.wikitext`, and record it in the notes as

```
stammbaum: {columns: [...], printed_under: "<headword on the scan>",
            points_at_it: "<the sentence that references it>"}
```

The main loop then works this skill for each flagged article.

## Don'ts

- **Do not touch `KURZTEXT`.** `RE:Acilius 20` ends its KURZTEXT with "mit Stammbaum", but
  that was an editor's doing; the standing rule that only `KORREKTURSTAND` changes wins.
- Do not invent links or people. Every box reproduces what the print shows; add an `[[RE:…]]`
  target only for an entry the print itself names.
- Keep the cell count of neighbouring rows consistent, and count 3 table columns per box
  against the 40-column cap before assembling a wide tree.

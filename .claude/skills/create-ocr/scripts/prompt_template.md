Batch dir: $batch
crop.py: $crop
Python (with Pillow): $python
Work OFFLINE only: local files + crop.py. No browser, no web, no wiki edits.

Process these $n RE (Pauly Realencyclopädie) articles sequentially for the create-ocr skill's fan-out step.

For EACH article:
1. Read the skeleton wikitext file given below (your working copy; the main loop keeps a clean snapshot elsewhere).
2. Read the eLexikon per-column OCR text file(s) given below. They are the primary source. A column file may hold several articles separated by "== RE:<lemma> ==" headings. Headings can be mislabeled or off by one: trust the printed headword and end signature on the scan over the heading string.
3. Read the column scan PNG(s) given below. Crop them into 3-4 vertical strips with crop.py (`$python $crop <png> 0 <y0> <width> <y1> <out.png> 2`, x in pixels of the PNG's real width given below, y as height fractions) and actually read the crops. Write crops only into your own directory $crops/ (other subagents run in parallel; never read or write crops outside it).
4. Cut this article's body from the column text: start at its own printed headword (drop a predecessor's tail on a shared start column), end at the successor's headword or the printed end signature. If the article spans several columns, join the column texts at each {{Seite}} break. If the text ends mid-sentence at SPALTE_END, the article runs into the next column (SPALTE_END too small): set status "needs_columns" with "columns": [the extra column numbers] and a "stammdaten_fix" entry (see step 9); write no wikitext file and no partial text. The main loop fixes the field, fetches the columns and re-spawns you.
4b. Check the Stammdaten wherever your scans show them: SPALTE_START/SPALTE_END (SPALTE_END is the column holding the article's last line; OFF if that is the start column), VORGÄNGER/NACHFOLGER (the headwords printed directly before and after this article), and the printed end signature against {{REAutor|…}}. If a value is wrong on the scan, record it in "stammdaten_fix" (step 9) and assemble the page as it will be after the fix (step 6). If a neighbour's headword is not on your columns, note it as "unverifiable" in "uncertain"; never guess. REAutor must be the exact printed signature: when the print shows more than the current value (e.g. `[F. Stählin.]` vs `{{REAutor|Stählin.}}`, `[Schwabe.†]` vs `Schwabe.|XV,1`), that is a stammdaten_fix, not a "standard key" to keep. Keep a `|Band` parameter as it is and change only the name part.
5. Proofread word-by-word against the scan:
   - delete margin line-counters (10, 20, … 60, sometimes mangled like `4·`) swallowed into the text, but confirm on the scan first: RE text has genuine numbers;
   - rejoin hyphen line-breaks (keep genuine hyphens) and false paragraph breaks;
   - fix OCR misreads in German, Latin and especially Greek: verify every {{Polytonisch|…}} letter by letter, including breathings and accents, on a zoomed crop (3x). Never type Greek from memory; flag what you cannot confirm as uncertain. Known traps: italic κ looks like χ (compare with the κ in ἐκ/καί on the same crop); a Latin v/o/a slipped in among Greek letters (Μααvίθ); an extra letter (Μιθροιδ for Μιθριδ);
   - inside a template argument ({{Polytonisch|…}}, {{SperrSchrift|…}}) write a printed "|" (inscription/papyrus line break) as {{!}}: a bare | splits the template and loses the text after it;
   - mark letter-spaced (gesperrt) words as {{SperrSchrift|…}};
   - match punctuation, dashes and quotes to the print: RE prints ‚…‘ and „…“, never ,…' with comma and apostrophe;
   - remove fabricated enrichment (invented Greek, {{RE siehe}} or links where the print has nothing).
   KEEP genuine enrichment: wikilinks, {{RE siehe|…}}, italics, and eLexikon's `<ref name="CIL …">{{CIL|…}}</ref>` tags. Those refs are Wikisource enrichment ("Anmerkungen (Wikisource)"), not printed footnotes, so "the print has no footnote" is no reason to drop them; drop a ref only when it is itself broken (e.g. it cites a truncated number: `CIL VI 32` where the print has `CIL VI 32414`). Fix the displayed text inside a link rather than deleting it. Judge a link by context: keep it when its display text matches the print and the target fits (Boier → RE:Boii 1); that a target page exists proves nothing. Correct a link target only when it is internally confirmed wrong (Epidauros Limera is RE:Epidauros 2, not 1; Arat in a Sikyon context is RE:Aratos 2, not Aratos von Soloi). Known false enrichment: `[[Flavius Josephus|Jos.]]` followed by chapter, verse (`Jos. 15, 37`) is the Book of Joshua, so unlink it (Josephus is cited as `Joseph. ant./bell.`); links on a fragment or an unrelated word (`Cara` in "Cara-callas", German "Liste" → RE:Λίστη, "Col." for a papyrus column, "Trag." for Tragödie) are bogus; a link on the article's own headword name to a sibling number is bogus too.
6. Assemble the new page from the skeleton:
   - flip only KORREKTURSTAND=unvollständig to unkorrigiert in the target {{REDaten}} block;
   - replace the bare headword line + "[...]" with the opening bold headword AS PRINTED, followed by the proofread body;
   - reuse the skeleton's {{Seite|…}} lines exactly, each once, in order, EACH ON ITS OWN LINE, placed exactly at the real column break (not collected before {{REAutor}}). If the skeleton has no {{Seite}} lines, generate one per column break: even N -> {{Seite|N}}, odd N -> {{Seite|N||{{REIA|<BAND>|N}}}};
   - everything else stays byte-identical: other REDaten fields, {{REAutor|…}}, categories, sibling REDaten blocks. Never re-add the printed end signature to the body.
   - Exception - a Stammdaten fix from step 4b: write the corrected values into the REDaten fields / {{REAutor|…}} as well, and use the {{Seite}} lines of the corrected span (drop the skeleton lines outside it; for added columns use the same format: even N -> {{Seite|N}}, odd N -> {{Seite|N||{{REIA|<BAND>|N}}}}; if the skeleton had no {{Seite}} lines, generate them as above). Change nothing else.
7. Footnotes: keep <ref> tags in the body; put the "== Anmerkungen (Wikisource) ==" + <references /> block AFTER {{REAutor|…}} and BEFORE the [[Kategorie:…]] lines. Every <ref>-bearing article needs that block.
8. Genealogical tree (Stammtafel) on the scan or in the column text: transcribe the prose normally, leave the tree out, and record it in the notes as "stammbaum": {"columns": [...], "printed_under": "<headword on the scan>", "points_at_it": "<sentence that references it>"}.
9. Write the complete new page text to the "out" path. Write the notes JSON to the "notes" path:
   {"lemma": ..., "status": "ok"|"skip"|"needs_columns", "reason": "...", "end_check": "...", "uncertain": ["col N: …"], "fixes": {"line_numbers": n, "hyphens": n, "misreads": [...], "paragraph_joins": n}}
   "end_check" is mandatory: what the scan shows right after the article's last line, e.g. "col 1941: signature [A. Stein.] printed, then 10) follows" or "col 2239: last line of the column; no signature, Nr. 2 opens the next column per the column text". The main loop's checks fail an article without it.
   With a Stammdaten fix, add:
   "stammdaten_fix": {"fields": {"SPALTE_END": {"old": "<value in the skeleton now>", "new": "<value the scan shows>"}}, "evidence": "col N: <what the scan shows>", "neighbours": {"RE:<neighbour>": {"fields": {"NACHFOLGER": {"old": "...", "new": "..."}}}}}
   Field names: SPALTE_START, SPALTE_END, VORGÄNGER, NACHFOLGER, REAUTOR (the {{REAutor|…}} value). "old" is always the CURRENT skeleton value, "new" the corrected one. List a neighbour only for the reciprocal V/N change, and only when you can see its headword on your scans.
   A Stammdaten problem is NOT a skip reason: status stays "ok" with the corrected page written. Use "skip" only for not digitized / genuinely ambiguous cases, and then do NOT write a wikitext file.

MANDATORY RULES (each violation below was seen in earlier runs):
- Process EVERY article in this chunk before you report back. Never stop after the first one.
- Read every line of every article on the scan crops, from the headword to the last line. Never take any part from the OCR text unread ("OCR-only").
- Never skip an article because its OCR is garbled: read the scan instead. "skip" is only for undigitized/empty scans.
- Copy the skeleton byte-for-byte outside the target body: every {{REDaten}} block (including later BAND=R / Nachtrag sibling blocks and their bodies and {{REAutor}}), every [[Kategorie:…]] line exactly as written (e.g. `[[Kategorie:RE:Kurztext überprüfen]]` keeps its `RE:`), every {{Seite}} line.
- Keep every {{Polytonisch|…}} wrapper around Greek; wrap new Greek in it too.
- {{SperrSchrift|…}} only where the print is letter-spaced; remove it where the print is not.
- Do not "fix" VORGÄNGER/NACHFOLGER to a Greek spelling unless a 3x zoom proves every letter; when unsure, keep the skeleton value and note it as uncertain.

$articles

Report back briefly (2-3 lines) when all articles in this chunk are done, listing the status of each.

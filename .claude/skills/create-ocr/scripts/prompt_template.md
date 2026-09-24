Batch dir: $batch
crop.py: $crop
Python (with Pillow): $python
Work OFFLINE only: local files + crop.py. No browser, no web, no wiki edits.

Process these $n RE (Pauly Realencyclopädie) articles sequentially for the create-ocr skill's fan-out step.

For EACH article:
1. Read the skeleton wikitext file given below (your working copy; the main loop keeps a clean snapshot elsewhere).
2. Read the eLexikon per-column OCR text file(s) given below. They are the primary source. A column file may hold several articles separated by "== RE:<lemma> ==" headings. Headings can be mislabeled or off by one: trust the printed headword and end signature on the scan over the heading string.
3. Read the column scan PNG(s) given below. Crop them into 3-4 vertical strips with crop.py (`$python $crop <png> 0 <y0> <width> <y1> <out.png> 2`, x in pixels of the PNG's real width given below, y as height fractions) and actually read the crops. Write crops only under $batch/crops/.
4. Cut this article's body from the column text: start at its own printed headword (drop a predecessor's tail on a shared start column), end at the successor's headword or the printed end signature. If the article spans several columns, join the column texts at each {{Seite}} break. If the text ends mid-sentence at SPALTE_END, the article probably runs into the next column (bad Stammdaten): set status "skip" with that reason; do not publish a partial text.
5. Proofread word-by-word against the scan:
   - delete margin line-counters (10, 20, … 60, sometimes mangled like `4·`) swallowed into the text, but confirm on the scan first: RE text has genuine numbers;
   - rejoin hyphen line-breaks (keep genuine hyphens) and false paragraph breaks;
   - fix OCR misreads in German, Latin and especially Greek: verify every {{Polytonisch|…}} letter by letter, including breathings and accents, on a zoomed crop. Never type Greek from memory; flag what you cannot confirm as uncertain;
   - mark letter-spaced (gesperrt) words as {{SperrSchrift|…}};
   - match punctuation, dashes and quotes to the print;
   - remove fabricated enrichment (invented Greek, bogus <ref>, {{RE siehe}} or links where the print has nothing).
   KEEP genuine enrichment: wikilinks, {{RE siehe|…}}, italics. Fix the displayed text inside a link rather than deleting it. Correct a link target only when it is internally confirmed wrong.
6. Assemble the new page from the skeleton:
   - flip only KORREKTURSTAND=unvollständig to unkorrigiert in the target {{REDaten}} block;
   - replace the bare headword line + "[...]" with the opening bold headword AS PRINTED, followed by the proofread body;
   - reuse the skeleton's {{Seite|…}} lines exactly, each once, in order, EACH ON ITS OWN LINE, placed exactly at the real column break (not collected before {{REAutor}}). If the skeleton has no {{Seite}} lines, generate one per column break: even N -> {{Seite|N}}, odd N -> {{Seite|N||{{REIA|<BAND>|N}}}};
   - everything else stays byte-identical: other REDaten fields, {{REAutor|…}}, categories, sibling REDaten blocks. Never re-add the printed end signature to the body.
7. Footnotes: keep <ref> tags in the body; put the "== Anmerkungen (Wikisource) ==" + <references /> block AFTER {{REAutor|…}} and BEFORE the [[Kategorie:…]] lines. Every <ref>-bearing article needs that block.
8. Genealogical tree (Stammtafel) on the scan or in the column text: transcribe the prose normally, leave the tree out, and record it in the notes as "stammbaum": {"columns": [...], "printed_under": "<headword on the scan>", "points_at_it": "<sentence that references it>"}.
9. Write the complete new page text to the "out" path. Write the notes JSON to the "notes" path:
   {"lemma": ..., "status": "ok"|"skip", "reason": "...", "uncertain": ["col N: …"], "fixes": {"line_numbers": n, "hyphens": n, "misreads": [...], "paragraph_joins": n}}
   For status "skip" (not digitized, ambiguous, Stammdaten problem) do NOT write a wikitext file.

$articles

Report back briefly (2-3 lines) when all articles in this chunk are done, listing the status of each.

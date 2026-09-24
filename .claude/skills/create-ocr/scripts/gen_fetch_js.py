#!/usr/bin/env python3
"""Generate browser_evaluate functions that fetch eLexikon column texts or scans.

Usage: gen_fetch_js.py <batch> --kind texts|scans [--chunk N]

Reads <batch>/columns.json, skips columns already present locally
(coltext/<BAND>_<col:04d>.txt or scans/<BAND>_<col:04d>.png), and writes
<batch>/fetch_js/<kind>_NN.js. Paste each file's content as the `function` of one
browser_evaluate call (after the Cloudflare warm-up) and save the result with the
`filename:` parameter to <batch>/fetch_js/<kind>_NN.result.json. Then:
  texts: save_coltexts.py <batch> <result.json>...
  scans: decode_b64_files.py <result.json> <batch>/scans
Each function returns {files: {name: text|base64}, errs: [...]} and stops early
after 3 consecutive HTTP errors (Cloudflare) - re-navigate, wait, and re-run this
script: already-saved columns are skipped, so it resumes where it stopped.
Default chunk: 25 texts / 10 scans per call (keeps results a few MB).
"""
import argparse
import glob
import json
import os
import urllib.parse

from common import col_key, load_json, scan_dir_letter

JS = """async () => {
  const items = %s;
  const kind = %s;
  const files = {};
  const errs = [];
  let consecutive = 0;
  for (const [name, url] of items) {
    try {
      const resp = await fetch(url, {credentials: 'include'});
      if (!resp.ok) throw new Error('HTTP ' + resp.status);
      if (kind === 'texts') {
        const doc = new DOMParser().parseFromString(await resp.text(), 'text/html');
        const pres = [...doc.querySelectorAll('div.ml15 pre')];
        if (!pres.length) throw new Error('no <pre> in page');
        files[name] = pres.pop().textContent;
      } else {
        const bytes = new Uint8Array(await resp.arrayBuffer());
        let bin = '';
        for (let i = 0; i < bytes.length; i += 8192) {
          bin += String.fromCharCode.apply(null, bytes.subarray(i, i + 8192));
        }
        files[name] = btoa(bin);
      }
      consecutive = 0;
    } catch (e) {
      errs.push(name + ': ' + e.message);
      if (++consecutive >= 3) { errs.push('ABORTED after 3 consecutive errors'); break; }
    }
    await new Promise(r => setTimeout(r, 700));
  }
  return {files, errs};
}
"""


def text_url(band, col):
    return f"https://elexikon.ch/?Typ=REt&Text={urllib.parse.quote(band.replace(' ', ''), safe=',')}_{col}"


def scan_url(band, col):
    return (f"https://elexikon.ch/meyers/REo/{scan_dir_letter(band)}/"
            f"{urllib.parse.quote(col_key(band, col), safe=',')}.png")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("batch")
    ap.add_argument("--kind", choices=("texts", "scans"), required=True)
    ap.add_argument("--chunk", type=int, default=0)
    args = ap.parse_args()
    b = args.batch
    chunk = args.chunk or (25 if args.kind == "texts" else 10)
    columns = load_json(os.path.join(b, "columns.json"))

    items = []
    for band, col in columns:
        if args.kind == "texts":
            name = col_key(band, col) + ".txt"
            if not os.path.exists(os.path.join(b, "coltext", name)):
                items.append((name, text_url(band, col)))
        else:
            name = col_key(band, col) + ".png"
            path = os.path.join(b, "scans", name)
            if not (os.path.exists(path) and os.path.getsize(path) > 0):
                items.append((name, scan_url(band, col)))

    outdir = os.path.join(b, "fetch_js")
    os.makedirs(outdir, exist_ok=True)
    for old in glob.glob(os.path.join(outdir, f"{args.kind}_*.js")):
        os.remove(old)
    n = 0
    for i in range(0, len(items), chunk):
        n += 1
        js = JS % (json.dumps(items[i:i + chunk], ensure_ascii=False), json.dumps(args.kind))
        with open(os.path.join(outdir, f"{args.kind}_{n:02d}.js"), "w", encoding="utf-8") as fh:
            fh.write(js)
    print(f"{len(items)} {args.kind} to fetch ({len(columns) - len(items)} already local) "
          f"-> {n} file(s) in {outdir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

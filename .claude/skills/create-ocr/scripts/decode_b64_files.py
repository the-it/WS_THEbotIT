#!/usr/bin/env python3
"""Decode a browser-fetched base64 batch into files.

Usage: decode_b64_files.py <batch.json> <outdir>

<batch.json> is what the in-browser fetch loop returned via the `filename:`
parameter: a JSON object mapping filename -> base64 content, e.g.
{"VII A,1_0752.png": "iVBORw0...", "Tubantes.txt": "..."} .
(A wrapping {"files": {...}} object is accepted too.)

PNG payloads are verified by magic number; everything is written into <outdir>
with the mapping key as filename (subdirectories are not allowed).
"""
import base64
import json
import os
import sys

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    batch_path, outdir = sys.argv[1], sys.argv[2]
    with open(batch_path, encoding="utf-8") as fh:
        data = json.load(fh)
    if isinstance(data, str):  # browser_evaluate saves JSON.stringify output re-quoted
        data = json.loads(data)
    if isinstance(data, dict) and isinstance(data.get("errs"), list) and data["errs"]:
        for e in data["errs"]:
            print(f"FETCH-ERR  {e}")
    if isinstance(data, dict) and isinstance(data.get("files"), dict):
        data = data["files"]
    if not isinstance(data, dict) or not data:
        print("ERROR: batch is not a non-empty filename->base64 object")
        return 1
    os.makedirs(outdir, exist_ok=True)
    failures = 0
    for name, b64 in data.items():
        base = os.path.basename(name)
        if base != name:
            print(f"SKIP  {name}: subdirectories not allowed")
            failures += 1
            continue
        try:
            blob = base64.b64decode(b64, validate=True)
        except Exception as exc:  # noqa: BLE001 - report and continue
            print(f"FAIL  {name}: base64 decode error: {exc}")
            failures += 1
            continue
        if name.lower().endswith(".png") and not blob.startswith(PNG_MAGIC):
            head = blob[:60]
            print(f"FAIL  {name}: not a PNG (starts with {head!r}) — Cloudflare block page?")
            failures += 1
            continue
        path = os.path.join(outdir, name)
        with open(path, "wb") as out:
            out.write(blob)
        print(f"OK    {name}  ({len(blob)} bytes)")
    print(f"done: {len(data) - failures}/{len(data)} written to {outdir}")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

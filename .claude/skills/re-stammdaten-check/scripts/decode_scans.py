#!/usr/bin/env python3
"""Decode a base64 scan batch (produced by the in-browser fetch loop) into real PNG files.

Usage:
    python3 decode_scans.py <b64_batch.json> <scansdir> <BANDPREFIX>

The browser download step (fetch each PNG with credentials:'include', base64-encode, save via
the evaluate `filename:` param) returns a JSON object like:
    { "525": {"status":200, "b64":"...", "len":123456}, "529": {"status":403}, ... }
(possibly wrapped in {"result": {...}}). Keys are page numbers.

This writes <scansdir>/<BANDPREFIX>_<page>.png for every status-200 entry, verifies each is a
valid PNG, and reports any failures. Example BANDPREFIX: "VIIIA,1" (BAND "VIII A,1" without
spaces). Native size is 3685×2592.
"""
import sys, json, base64, os

try:
    from PIL import Image
    HAVE_PIL = True
except ImportError:
    HAVE_PIL = False


def main():
    if len(sys.argv) < 4:
        print(__doc__)
        sys.exit(1)
    b64path, scansdir, prefix = sys.argv[1], sys.argv[2].rstrip('/'), sys.argv[3]
    os.makedirs(scansdir, exist_ok=True)
    d = json.load(open(b64path))
    if isinstance(d, str):  # evaluate returned JSON.stringify(...) -> double-encoded
        d = json.loads(d)
    if isinstance(d, dict) and 'result' in d and isinstance(d['result'], dict):
        d = d['result']

    ok, fail = 0, []
    for page, v in d.items():
        if isinstance(v, dict) and v.get('status') == 200 and v.get('b64'):
            out = f'{scansdir}/{prefix}_{page}.png'
            open(out, 'wb').write(base64.b64decode(v['b64']))
            if HAVE_PIL:
                try:
                    Image.open(out).verify()
                except Exception as e:
                    fail.append((page, f'corrupt: {e}'))
                    continue
            ok += 1
        else:
            fail.append((page, v.get('status') if isinstance(v, dict) else v))
    print(f'decoded {ok} PNGs into {scansdir} (prefix {prefix}); failures: {fail}')


if __name__ == '__main__':
    main()

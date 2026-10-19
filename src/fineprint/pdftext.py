"""Minimal stdlib, page-aware text-layer extraction for FDA PDFs (citation lookup only).

Handles uncompressed and object-stream objects and Flate content streams with
literal-string Tj/TJ operators. It does not OCR images: text that exists only as
pixels (e.g. redacted establishment tables) is reported as not found, never guessed.
"""

from __future__ import annotations

import re
import zlib

_ESC = {b"n": b"\n", b"r": b"", b"t": b" ", b"b": b"", b"f": b"", b"(": b"(", b")": b")", b"\\": b"\\"}


def _strings(seg: bytes) -> bytes:
    out = []
    for m in re.finditer(rb"\((?:\\.|[^\\)])*\)", seg, flags=re.S):
        s = m.group(0)[1:-1]
        s = re.sub(rb"\\([0-7]{1,3})", lambda x: bytes([int(x.group(1), 8) & 255]), s)
        s = re.sub(rb"\\([nrtbf()\\])", lambda x: _ESC[x.group(1)], s)
        out.append(s)
    return b"".join(out)


def _objects(b: bytes) -> dict[int, bytes]:
    objs = {int(m.group(1)): m.group(2) for m in re.finditer(rb"(\d+) 0 obj(.*?)endobj", b, flags=re.S)}
    for body in list(objs.values()):
        if b"/ObjStm" not in body:
            continue
        sm = re.search(rb"stream\r?\n(.*)\r?\nendstream", body, flags=re.S)
        try:
            data = zlib.decompress(sm.group(1))
        except Exception:
            continue
        n = int(re.search(rb"/N (\d+)", body).group(1))
        first = int(re.search(rb"/First (\d+)", body).group(1))
        hdr = data[:first].split()
        pairs = [(int(hdr[i]), int(hdr[i + 1])) for i in range(0, 2 * n, 2)]
        for k, (onum, off) in enumerate(pairs):
            end = pairs[k + 1][1] if k + 1 < len(pairs) else len(data) - first
            objs.setdefault(onum, data[first + off: first + end])
    return objs


def page_texts(pdf_bytes: bytes) -> list[str]:
    """Return the text layer of each page, in page order (index 0 == page 1)."""
    objs = _objects(pdf_bytes)
    root = int(re.search(rb"/Root (\d+) 0 R", pdf_bytes).group(1))
    pages_ref = int(re.search(rb"/Pages (\d+) 0 R", objs[root]).group(1))
    order: list[int] = []

    def walk(n):
        o = objs[n]
        if re.search(rb"/Type\s*/Pages", o):
            for k in re.findall(rb"(\d+) 0 R", re.search(rb"/Kids\s*\[(.*?)\]", o, flags=re.S).group(1)):
                walk(int(k))
        else:
            order.append(n)

    walk(pages_ref)
    texts = []
    for pn in order:
        cm = re.search(rb"/Contents\s*(\[(.*?)\]|(\d+) 0 R)", objs[pn], flags=re.S)
        refs = [int(x) for x in re.findall(rb"(\d+) 0 R", cm.group(1))] if cm else []
        parts = []
        for r in refs:
            sm = re.search(rb"stream\r?\n(.*)\r?\nendstream", objs.get(r, b""), flags=re.S)
            if not sm:
                continue
            try:
                d = zlib.decompress(sm.group(1))
            except Exception:
                continue
            parts.append(" ".join(_strings(t).decode("latin-1") for t in re.findall(rb"BT(.*?)ET", d, flags=re.S)))
        texts.append(re.sub(r"\s+", " ", " ".join(parts)).strip())
    return texts


def find(pdf_bytes: bytes, needles: list[str], before: int = 160, after: int = 160) -> dict:
    pages = page_texts(pdf_bytes)
    hits = {n: [] for n in needles}
    for i, t in enumerate(pages, 1):
        for n in needles:
            j = t.find(n)
            if j >= 0:
                hits[n].append({"page": i, "excerpt": t[max(0, j - before): j + len(n) + after]})
    return {"pages": len(pages), "hits": hits}

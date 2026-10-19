"""Resumable, checksum-verified downloads of multi-GB release parts.

* Bytes go to ``<dest>.part`` with a sidecar ``<dest>.part.json`` pinning the ETag.
* Resume uses ``Range`` + ``If-Range: <etag>``: a changed object answers 200 and the
  partial file is discarded instead of being spliced with the new release.
* Completion requires length == Content-Length and MD5 == advertised (when given);
  only then is the file renamed to ``dest`` and a ``<dest>.json`` provenance record
  written. A failed verification leaves no file at ``dest``.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

from . import net

CHUNK = 8 << 20


class DownloadInterrupted(Exception):
    """Raised by the test hook ``stop_after_bytes`` to simulate a dropped connection."""


class VerificationFailed(Exception):
    pass


def hash_file(path: Path, chunk: int = CHUNK) -> tuple[str, str, int]:
    sha, md5, n = hashlib.sha256(), hashlib.md5(), 0
    with open(path, "rb") as fh:
        while True:
            b = fh.read(chunk)
            if not b:
                break
            sha.update(b)
            md5.update(b)
            n += len(b)
    return sha.hexdigest(), md5.hexdigest(), n


def _write_json(path: Path, obj) -> None:
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2) + "\n", encoding="utf-8", newline="\n")
    os.replace(tmp, path)


def download(url: str, dest: Path, *, expected_md5: str | None = None, retries: int = 8,
             timeout: float = 120, stop_after_bytes: int | None = None, log=print) -> dict:
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    part = dest.with_name(dest.name + ".part")
    side = dest.with_name(dest.name + ".part.json")
    record_path = dest.with_name(dest.name + ".json")

    head = net.fetch(url, method="HEAD", timeout=timeout)
    size = int(head.headers["content-length"])
    etag = head.headers.get("etag")

    if dest.exists():
        rec = json.loads(record_path.read_text(encoding="utf-8")) if record_path.exists() else None
        if rec and rec.get("etag") == etag and rec.get("bytes") == size == dest.stat().st_size:
            t0 = time.perf_counter()
            sha, md5, n = hash_file(dest)
            if sha == rec["sha256"] and (expected_md5 is None or md5 == expected_md5):
                rec["reverified_at"] = net.utc_now()
                rec["reverify_seconds"] = round(time.perf_counter() - t0, 2)
                rec["status"] = "verified_existing"
                return rec
        raise VerificationFailed(f"{dest} exists but does not match the live object; move it aside first")

    state = {"url": url, "etag": etag, "content_length": size, "segments": []}
    if part.exists() and side.exists():
        prev = json.loads(side.read_text(encoding="utf-8"))
        if prev.get("etag") == etag and prev.get("url") == url:
            state = prev
        else:
            part.unlink()
    elif part.exists():
        part.unlink()
    state.setdefault("first_started_at", net.utc_now())

    attempts = 0
    while True:
        have = part.stat().st_size if part.exists() else 0
        if have > size:
            raise VerificationFailed(f"partial file larger than object: {have} > {size}")
        if have == size:
            break
        attempts += 1
        headers = {"User-Agent": net.USER_AGENT}
        if have:
            headers["Range"] = f"bytes={have}-"
            if etag:
                headers["If-Range"] = etag
        seg = {"started_at": net.utc_now(), "from_byte": have}
        t0 = time.perf_counter()
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                if have and resp.status == 200:
                    # Object changed (If-Range failed): never splice two releases.
                    log(f"{dest.name}: server returned full object on resume; restarting from 0")
                    have = 0
                    mode = "wb"
                elif have and resp.status != 206:
                    raise IOError(f"unexpected status {resp.status} on resume")
                else:
                    mode = "ab" if have else "wb"
                got = 0
                with open(part, mode) as out:
                    while True:
                        b = resp.read(CHUNK)
                        if not b:
                            break
                        out.write(b)
                        got += len(b)
                        if stop_after_bytes is not None and have + got >= stop_after_bytes:
                            out.flush()
                            seg.update(to_byte=have + got, seconds=round(time.perf_counter() - t0, 2),
                                       interrupted="test_hook")
                            state["segments"].append(seg)
                            _write_json(side, state)
                            raise DownloadInterrupted(f"stopped after {have + got} bytes (test hook)")
            seg.update(to_byte=have + got, seconds=round(time.perf_counter() - t0, 2), http_status=resp.status)
            state["segments"].append(seg)
            _write_json(side, state)
        except DownloadInterrupted:
            raise
        except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as e:
            seg.update(error=f"{type(e).__name__}: {e}", seconds=round(time.perf_counter() - t0, 2),
                       to_byte=part.stat().st_size if part.exists() else 0)
            state["segments"].append(seg)
            _write_json(side, state)
            if attempts > retries:
                raise
            log(f"{dest.name}: {seg['error']}; retrying from byte {seg['to_byte']}")
            time.sleep(min(60, 2 ** attempts))

    t0 = time.perf_counter()
    sha, md5, n = hash_file(part)
    hash_s = round(time.perf_counter() - t0, 2)
    if n != size:
        raise VerificationFailed(f"length {n} != Content-Length {size}")
    if expected_md5 is not None and md5 != expected_md5:
        bad = part.with_name(part.name + ".md5-mismatch")
        os.replace(part, bad)
        raise VerificationFailed(f"MD5 {md5} != advertised {expected_md5}; kept as {bad.name}")
    os.replace(part, dest)
    xfer = [s for s in state["segments"] if "to_byte" in s and "seconds" in s]
    rec = {
        "url": url, "final_url": head.final_url, "etag": etag,
        "last_modified": head.headers.get("last-modified"), "x_amz_version_id": head.headers.get("x-amz-version-id"),
        "content_length": size, "bytes": n, "sha256": sha, "md5": md5,
        "expected_md5": expected_md5, "md5_matches_advertised": None if expected_md5 is None else md5 == expected_md5,
        "first_started_at": state["first_started_at"], "completed_at": net.utc_now(),
        "segments": state["segments"], "resumed": len(state["segments"]) > 1,
        "transfer_seconds": round(sum(s["seconds"] for s in xfer), 2),
        "hash_seconds": hash_s, "status": "downloaded",
    }
    _write_json(record_path, rec)
    side.unlink(missing_ok=True)
    return rec

"""HTTP helpers with provenance: polite GET-to-file with hashing, and a seekable
HTTP Range reader so a remote multi-GB ZIP can be inspected without downloading it.

Every fetch returns the retrieval timestamp separately from any publication date;
callers must never substitute one for the other.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import io
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

# Deliberately generic: no personal data in request headers.
USER_AGENT = "fineprint-dst00/0.1 (research prototype; stdlib urllib)"

# Response headers worth keeping as provenance.
KEEP_HEADERS = (
    "content-type",
    "content-length",
    "content-disposition",
    "content-range",
    "last-modified",
    "etag",
    "accept-ranges",
    "x-dailymed-label-last-updated",
    "x-amz-version-id",
)

RETRY_STATUS = {429, 500, 502, 503, 504}


def utc_now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass
class FetchResult:
    url: str
    final_url: str
    status: int
    retrieved_at: str
    headers: dict = field(default_factory=dict)
    bytes: int = 0
    sha256: str = ""
    md5: str = ""
    path: str | None = None
    body: bytes | None = None
    elapsed_s: float = 0.0

    def provenance(self) -> dict:
        d = {k: v for k, v in self.__dict__.items() if k != "body"}
        return d


def _keep(headers) -> dict:
    return {k.lower(): v for k, v in headers.items() if k.lower() in KEEP_HEADERS}


def _open(req: urllib.request.Request, timeout: float, retries: int):
    delay = 2.0
    for attempt in range(retries + 1):
        try:
            return urllib.request.urlopen(req, timeout=timeout)
        except urllib.error.HTTPError as e:
            if e.code in RETRY_STATUS and attempt < retries:
                time.sleep(delay)
                delay *= 2
                continue
            raise
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            if attempt < retries:
                time.sleep(delay)
                delay *= 2
                continue
            raise


def fetch(
    url: str,
    dest: str | os.PathLike | None = None,
    *,
    max_bytes: int | None = None,
    timeout: float = 120,
    retries: int = 3,
    method: str = "GET",
    extra_headers: dict | None = None,
    chunk: int = 1 << 20,
) -> FetchResult:
    """GET (or HEAD) a URL, hashing while streaming.

    With ``dest`` the body is streamed to ``dest`` via a temp file and renamed
    atomically; otherwise it is kept in memory (``max_bytes`` caps either way).
    """
    headers = {"User-Agent": USER_AGENT}
    if extra_headers:
        headers.update(extra_headers)
    req = urllib.request.Request(url, headers=headers, method=method)
    t0 = time.perf_counter()
    retrieved_at = utc_now()
    resp = _open(req, timeout, retries)
    res = FetchResult(url=url, final_url=resp.geturl(), status=resp.status,
                      retrieved_at=retrieved_at, headers=_keep(resp.headers))
    if method == "HEAD":
        resp.close()
        res.elapsed_s = time.perf_counter() - t0
        return res
    sha, md5 = hashlib.sha256(), hashlib.md5()
    n = 0
    sink: io.BufferedWriter | io.BytesIO
    tmp = None
    if dest is not None:
        dest = Path(dest)
        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp = dest.with_name(dest.name + ".part")
        sink = open(tmp, "wb")
    else:
        sink = io.BytesIO()
    try:
        with resp:
            while True:
                buf = resp.read(chunk)
                if not buf:
                    break
                n += len(buf)
                if max_bytes is not None and n > max_bytes:
                    raise ValueError(f"response exceeds max_bytes={max_bytes}: {url}")
                sha.update(buf)
                md5.update(buf)
                sink.write(buf)
        declared = res.headers.get("content-length")
        if declared is not None and int(declared) != n:
            raise IOError(f"short read: got {n} of {declared} bytes from {url}")
    except BaseException:
        sink.close()
        if tmp is not None and tmp.exists():
            tmp.unlink()
        raise
    if dest is not None:
        sink.close()
        os.replace(tmp, dest)
        res.path = str(dest)
    else:
        res.body = sink.getvalue()
    res.bytes, res.sha256, res.md5 = n, sha.hexdigest(), md5.hexdigest()
    res.elapsed_s = time.perf_counter() - t0
    return res


class RemoteChangedError(IOError):
    pass


class HttpRangeReader(io.RawIOBase):
    """Read-only seekable file over HTTP Range requests.

    Pins the object's ETag from the initial HEAD and refuses any 206 response
    whose ETag differs, so a release replaced mid-inspection cannot be mixed.
    Small reads are served from a read-ahead block; large reads fetch exactly.
    """

    def __init__(self, url: str, *, block: int = 1 << 20, timeout: float = 120, retries: int = 3):
        super().__init__()
        self.url = url
        self.block = block
        self.timeout = timeout
        self.retries = retries
        head = fetch(url, method="HEAD", timeout=timeout, retries=retries)
        self.head = head
        self.size = int(head.headers["content-length"])
        self.etag = head.headers.get("etag")
        if head.headers.get("accept-ranges", "").lower() != "bytes":
            raise IOError(f"server does not advertise byte ranges: {url}")
        self._pos = 0
        self._cache_start = -1
        self._cache = b""
        self.requests = 0
        self.bytes_fetched = 0
        self.fetch_seconds = 0.0

    def readable(self):
        return True

    def seekable(self):
        return True

    def tell(self):
        return self._pos

    def seek(self, offset, whence=io.SEEK_SET):
        if whence == io.SEEK_SET:
            pos = offset
        elif whence == io.SEEK_CUR:
            pos = self._pos + offset
        elif whence == io.SEEK_END:
            pos = self.size + offset
        else:
            raise ValueError(whence)
        if pos < 0:
            raise ValueError("negative seek")
        self._pos = pos
        return pos

    def _get(self, start: int, end_inclusive: int) -> bytes:
        req = urllib.request.Request(
            self.url, headers={"User-Agent": USER_AGENT, "Range": f"bytes={start}-{end_inclusive}"})
        t0 = time.perf_counter()
        resp = _open(req, self.timeout, self.retries)
        with resp:
            if resp.status != 206:
                raise IOError(f"expected 206, got {resp.status} for range {start}-{end_inclusive}")
            etag = resp.headers.get("ETag")
            if self.etag and etag and etag != self.etag:
                raise RemoteChangedError(f"ETag changed {self.etag} -> {etag}: {self.url}")
            data = resp.read()
        self.fetch_seconds += time.perf_counter() - t0
        want = end_inclusive - start + 1
        if len(data) != want:
            raise IOError(f"range short read: {len(data)} != {want}")
        self.requests += 1
        self.bytes_fetched += len(data)
        return data

    def read(self, n=-1):
        if self._pos >= self.size:
            return b""
        if n is None or n < 0:
            n = self.size - self._pos
        n = min(n, self.size - self._pos)
        if n == 0:
            return b""
        cs = self._cache_start
        if cs >= 0 and cs <= self._pos and self._pos + n <= cs + len(self._cache):
            off = self._pos - cs
            out = self._cache[off:off + n]
        elif n >= self.block:
            out = self._get(self._pos, self._pos + n - 1)
        else:
            end = min(self.size, self._pos + self.block) - 1
            self._cache = self._get(self._pos, end)
            self._cache_start = self._pos
            out = self._cache[:n]
        self._pos += len(out)
        return out

    def readinto(self, b):
        data = self.read(len(b))
        b[: len(data)] = data
        return len(data)

    def stats(self) -> dict:
        return {"url": self.url, "size": self.size, "etag": self.etag, "range_requests": self.requests,
                "bytes_fetched": self.bytes_fetched, "fetch_seconds": round(self.fetch_seconds, 3)}

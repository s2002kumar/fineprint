"""Defensive ZIP traversal for untrusted DailyMed archives.

Nothing is ever extracted to disk by name. Members are streamed with hard byte
caps (declared sizes can lie), names are checked for traversal/absolute paths,
and suspicious compression ratios are reported rather than silently trusted.
"""

from __future__ import annotations

import io
import re
import zipfile
from dataclasses import dataclass

MiB = 1 << 20


@dataclass(frozen=True)
class Limits:
    max_members: int = 200_000
    max_member_bytes: int = 1024 * MiB   # nested SPL zip, decompressed
    max_xml_bytes: int = 256 * MiB       # a single SPL XML, decompressed
    max_ratio: float = 200.0             # flag if uncompressed/compressed exceeds this...
    ratio_min_bytes: int = 10 * MiB      # ...for members at least this large
    max_nested_members: int = 5_000


DEFAULT_LIMITS = Limits()


class ZipSafetyError(Exception):
    """A member breached a hard limit; the member must be treated as failed."""


_DRIVE = re.compile(r"^[A-Za-z]:")


def name_problems(name: str) -> list[str]:
    """Return reasons a member name is unsafe (empty list == acceptable)."""
    problems = []
    if not name:
        problems.append("empty_name")
    if "\x00" in name:
        problems.append("nul_in_name")
    if name.startswith(("/", "\\")) or _DRIVE.match(name):
        problems.append("absolute_path")
    if "\\" in name:
        problems.append("backslash_in_name")
    if any(seg == ".." for seg in re.split(r"[\\/]", name)):
        problems.append("parent_traversal")
    return problems


def member_problems(info: zipfile.ZipInfo, limits: Limits = DEFAULT_LIMITS) -> list[str]:
    problems = name_problems(info.filename)
    if info.flag_bits & 0x1:
        problems.append("encrypted")
    if info.file_size > limits.max_member_bytes:
        problems.append("declared_size_over_limit")
    if (info.file_size >= limits.ratio_min_bytes and info.compress_size > 0
            and info.file_size / info.compress_size > limits.max_ratio):
        problems.append("suspicious_compression_ratio")
    return problems


class BoundedReader(io.RawIOBase):
    """Wrap a binary stream; raise ZipSafetyError once more than ``limit`` bytes are read."""

    def __init__(self, raw, limit: int):
        super().__init__()
        self._raw = raw
        self._limit = limit
        self.count = 0

    def readable(self):
        return True

    def readinto(self, b):
        want = min(len(b), self._limit - self.count + 1)
        data = self._raw.read(want)
        self.count += len(data)
        if self.count > self._limit:
            raise ZipSafetyError(f"stream exceeded {self._limit} bytes")
        b[: len(data)] = data
        return len(data)


def read_member(zf: zipfile.ZipFile, info: zipfile.ZipInfo, limit: int) -> bytes:
    """Read one member fully (CRC checked by zipfile) without exceeding ``limit`` bytes."""
    if info.file_size > limit:
        raise ZipSafetyError(f"{info.filename}: declared {info.file_size} > limit {limit}")
    with zf.open(info) as fh:
        data = BoundedReader(fh, limit).read()
    return data


def open_member(zf: zipfile.ZipFile, info: zipfile.ZipInfo, limit: int) -> io.BufferedReader:
    if info.file_size > limit:
        raise ZipSafetyError(f"{info.filename}: declared {info.file_size} > limit {limit}")
    return io.BufferedReader(BoundedReader(zf.open(info), limit))


def scan_directory(zf: zipfile.ZipFile, limits: Limits = DEFAULT_LIMITS) -> dict:
    """Central-directory audit: counts, duplicates and unsafe members (no data read)."""
    infos = zf.infolist()
    if len(infos) > limits.max_members:
        raise ZipSafetyError(f"{len(infos)} members > max_members {limits.max_members}")
    seen, dups, flagged = set(), [], {}
    for i in infos:
        if i.filename in seen:
            dups.append(i.filename)
        seen.add(i.filename)
        p = member_problems(i, limits)
        if p:
            flagged[i.filename] = p
    return {
        "members": len(infos),
        "directories": sum(1 for i in infos if i.is_dir()),
        "compressed_bytes": sum(i.compress_size for i in infos),
        "uncompressed_bytes": sum(i.file_size for i in infos),
        "duplicate_names": dups,
        "flagged": flagged,
    }

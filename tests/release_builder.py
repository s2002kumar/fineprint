"""Build small on-disk 'release parts' (outer ZIP of nested SPL ZIPs) + manifest for ingest tests."""

import hashlib
import io
import json
import warnings
import zipfile
from pathlib import Path

from fineprint import download
from tests import FIXTURES

CURRENT = FIXTURES / "current"
FIX = {
    "lower_mfg": "2b0b9cc4-fca7-4e84-8d9d-0f9852528579",
    "multi_est": "3c5101a0-0c7e-4078-8dc3-a57beb9a0e92",
    "no_est": "99da5233-2760-46f6-8fb3-d9df5da70bfb",
    "kit": "3bda5cd1-df3c-4b4c-9868-cbc41f66f5a6",
}


def xml(key):
    return (CURRENT / f"{FIX[key]}.xml").read_bytes()


def nested(xml_bytes, xml_name="doc.xml"):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr(xml_name, xml_bytes)
        z.writestr("image-01.jpg", b"\xff\xd8\xff\xe0 not a real jpeg")
    return buf.getvalue()


def member(set_id, date="20261016"):
    return f"prescription/{date}_{set_id}.zip"


def standard_members():
    conflict = xml("lower_mfg").replace(b"</document>", b"<!-- variant bytes, same set/version -->\n</document>")
    return [
        (member(FIX["lower_mfg"]), nested(xml("lower_mfg"))),
        (member(FIX["multi_est"]), nested(xml("multi_est"))),
        (member(FIX["no_est"]), nested(xml("no_est"))),
        (member(FIX["kit"]), nested(xml("kit"))),
        (member(FIX["lower_mfg"], "20261017"), nested(conflict)),            # same set/version, different bytes
        (member("00000000-0000-0000-0000-00000000c0de"), b"PK\x03\x04 corrupt nested zip"),
        (member("00000000-0000-0000-0000-0000000bad01"), nested(xml("no_est")[:4000])),  # truncated XML
        ("prescription/../escape.zip", nested(xml("no_est"))),               # unsafe outer name
    ]


def write_part(path: Path, members, *, url="https://example.invalid/part.zip"):
    path.parent.mkdir(parents=True, exist_ok=True)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        with zipfile.ZipFile(path, "w", zipfile.ZIP_STORED) as z:
            for name, data in members:
                z.writestr(name, data)
    sha, md5, n = download.hash_file(path)
    record = {"url": url, "etag": f'"{md5}"', "last_modified": None, "content_length": n, "bytes": n,
              "sha256": sha, "md5": md5, "md5_matches_advertised": True, "first_started_at": None,
              "completed_at": "2026-10-19T00:00:00Z", "status": "downloaded"}
    Path(str(path) + ".json").write_text(json.dumps(record), encoding="utf-8")
    return {"name": path.name, "https_url": url, "advertised_number_of_files": len(members),
            "advertised_file_size": f"{n}B", "advertised_md5": md5, "advertised_last_modified": "2026-10-16",
            "local_path": path.resolve().as_posix()}


def write_manifest(root: Path, parts_members: dict) -> Path:
    parts = [write_part(root / name, members) for name, members in parts_members.items()]
    man = {"advertised_last_modified_values": ["2026-10-16"], "parts": parts, "zip_metadata": None}
    p = root / "release_manifest.json"
    p.write_text(json.dumps(man), encoding="utf-8")
    return p


def sha256(b):
    return hashlib.sha256(b).hexdigest()

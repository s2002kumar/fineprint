"""Source-manifest records.

Each record separates three time dimensions that must never be conflated:
``published_at`` (what the source/publisher asserts, may be None), ``retrieved_at``
(when we fetched it) and ``captured_at`` (third-party archive capture, if any).
``source_role`` is one of: current, historical, identity_historical,
identity_current, documentation, outcome (outcome sources are sealed in DST-00).
"""

from __future__ import annotations

import json
from pathlib import Path

ROLES = {"current", "historical", "identity_historical", "identity_current", "documentation", "outcome"}


def source_record(fetch_result, *, kind: str, role: str, data_dir: Path | None = None,
                  published_at: str | None = None, published_at_basis: str | None = None,
                  captured_at: str | None = None, **extra) -> dict:
    if role not in ROLES:
        raise ValueError(f"unknown source_role {role}")
    p = fetch_result.provenance()
    local = p.get("path")
    if local and data_dir is not None:
        try:
            local = Path(local).resolve().relative_to(Path(data_dir).resolve()).as_posix()
        except ValueError:
            pass
    rec = {
        "kind": kind,
        "source_role": role,
        "url": p["url"],
        "final_url": p["final_url"],
        "http_status": p["status"],
        "published_at": published_at,
        "published_at_basis": published_at_basis,
        "captured_at": captured_at,
        "retrieved_at": p["retrieved_at"],
        "bytes": p["bytes"],
        "sha256": p["sha256"],
        "md5": p["md5"],
        "response_headers": p["headers"],
        "local_path_in_data_dir": local,
    }
    rec.update(extra)
    return rec


def write_json(path: Path, obj) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False, sort_keys=False) + "\n", encoding="utf-8")

"""Synthetic SPL documents and FDA registration files with fully controlled contents."""

import hashlib
import io
import json
import zipfile
from pathlib import Path

from fineprint import spl

DECRS_HEADER = ["FEI_NUMBER", "DUNS_NUMBER", "FIRM_NAME", "ADDRESS", "EXPIRATION_DATE", "OPERATIONS",
                "ESTABLISHMENT_CONTACT_NAME", "ESTABLISHMENT_CONTACT_EMAIL", "AGENT_DETAILS", "REGISTRANT_NAME",
                "REGISTRANT_DUNS", "REGISTRANT_CONTACT_NAME", "REGISTRANT_CONTACT_EMAIL", "EXCLUSION_FLAG"]


def spl_xml(set_id, version, *, labeler_duns="111111111", products=(), establishments=(), with_block=True,
            note=""):
    """products: [(code, name, [package codes])]; establishments: [(duns, name, [(op_code, op_name, [codes])])]."""
    ests = ""
    for duns, name, ops in establishments:
        perf = ""
        for code, opname, prods in ops:
            pp = "".join(f'<product><manufacturedProduct><manufacturedMaterialKind><code code="{c}" '
                         f'codeSystem="2.16.840.1.113883.6.69"/></manufacturedMaterialKind></manufacturedProduct>'
                         f'</product>' for c in prods)
            perf += f'<performance><actDefinition><code code="{code}" displayName="{opname}"/>{pp}</actDefinition></performance>'
        idx = f'<id root="{spl.DUNS_ROOT}" extension="{duns}"/>' if duns else ""
        ests += f"<assignedEntity><assignedOrganization>{idx}<name>{name}</name></assignedOrganization>{perf}</assignedEntity>"
    block = f"<assignedEntity><assignedOrganization>{ests}</assignedOrganization></assignedEntity>" if with_block else ""
    subj = ""
    for code, name, pkgs in products:
        pk = "".join(f'<asContent><quantity><numerator value="1" unit="1"/></quantity><containerPackagedProduct>'
                     f'<code code="{p}" codeSystem="2.16.840.1.113883.6.69"/><formCode displayName="VIAL"/>'
                     f'</containerPackagedProduct></asContent>' for p in pkgs)
        subj += (f'<subject><manufacturedProduct><manufacturedProduct><code code="{code}" '
                 f'codeSystem="2.16.840.1.113883.6.69"/><name>{name}</name><formCode displayName="INJECTION"/>'
                 f'{pk}</manufacturedProduct></manufacturedProduct></subject>')
    return (f'<?xml version="1.0" encoding="UTF-8"?>\n<document xmlns="urn:hl7-org:v3"><id root="doc-{set_id}-{version}"/>'
            f'<code code="34391-3" displayName="HUMAN PRESCRIPTION DRUG LABEL"/><effectiveTime value="20260101"/>'
            f'<setId root="{set_id}"/><versionNumber value="{version}"/><author><assignedEntity>'
            f'<representedOrganization><id root="{spl.DUNS_ROOT}" extension="{labeler_duns}"/><name>Labeler Co</name>'
            f'{block}</representedOrganization></assignedEntity></author><component><structuredBody><component>'
            f'<section><code code="48780-1"/>{subj}</section></component></structuredBody></component>'
            f'<!--{note}--></document>').encode()


def nested(xml_bytes):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("doc.xml", xml_bytes)
    return buf.getvalue()


def write_zip_text(path: Path, member: str, text: str, date_time=(2026, 10, 19, 3, 0, 0)) -> dict:
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr(zipfile.ZipInfo(member, date_time=date_time), text)
    b = path.read_bytes()
    rec = {"url": f"https://example.invalid/{path.name}", "etag": None, "last_modified": None, "content_length": len(b),
           "bytes": len(b), "sha256": hashlib.sha256(b).hexdigest(), "md5": hashlib.md5(b).hexdigest(),
           "md5_matches_advertised": True, "first_started_at": None, "completed_at": "2026-10-20T00:00:00Z"}
    Path(str(path) + ".json").write_text(json.dumps(rec), encoding="utf-8")
    return rec


def decrs_text(rows):
    """rows: dicts with any of FEI_NUMBER/DUNS_NUMBER/FIRM_NAME/ADDRESS/EXPIRATION_DATE/EXCLUSION_FLAG.

    Contact columns are filled with obviously fake values so tests can prove they are dropped.
    """
    lines = ["\t".join(DECRS_HEADER)]
    for r in rows:
        full = {"OPERATIONS": "MANUFACTURE", "EXCLUSION_FLAG": "N", "ESTABLISHMENT_CONTACT_NAME": "Test Person",
                "ESTABLISHMENT_CONTACT_EMAIL": "person@example.invalid", "AGENT_DETAILS": "agent detail",
                "REGISTRANT_CONTACT_NAME": "Test Person", "REGISTRANT_CONTACT_EMAIL": "person@example.invalid", **r}
        lines.append("\t".join(full.get(h, "") for h in DECRS_HEADER))
    return "\n".join(lines) + "\n"

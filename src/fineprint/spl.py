"""Streaming extraction of establishment operations and product/package codes from SPL XML.

Design rules (spec v1.3):
* Raw values are kept verbatim; nothing is padded, guessed or inferred.
* Organizations are recorded by their position in the author hierarchy:
  depth 1 = labeler (a company, NOT a site), depth 2 = registrant,
  depth 3 = establishment (the only level whose performance elements are
  operations). Anything else is reported as an anomaly, not silently used.
* Operations keep the raw NCI code AND displayName; no operation is mapped onto
  another (PACK/LABEL never become MANUFACTURE).
* Every extracted item carries an indexed XPath-like ``loc`` into the source XML.
* Memory is bounded per document: narrative sections are cleared as they end.
"""

from __future__ import annotations

import hashlib
import io
import xml.etree.ElementTree as ET
from dataclasses import dataclass

HL7 = "urn:hl7-org:v3"
DUNS_ROOT = "1.3.6.1.4.1.519.1"
FEI_ROOT = "2.16.840.1.113883.4.82"
NDC_SYSTEM = "2.16.840.1.113883.6.69"
PRODUCT_DATA_SECTION = "48780-1"

ORG_ROLE_BY_DEPTH = {1: "labeler", 2: "registrant", 3: "establishment"}

# Finished-dosage MANUFACTURE operation code as observed in archived Hospira SPLs
# (DST-00). "API MANUFACTURE" (C82401) etc. are distinct operations, never aliases.
MANUFACTURE_CODE = "C43360"

# Element-name alternatives across SPL generations (pre-2009 R4 used *Medicine).
_PRODUCT_INNER = ("manufacturedProduct", "manufacturedMedicine")
_PACKAGE = ("containerPackagedProduct", "containerPackagedMedicine")

DEFAULT_MAX_XML_BYTES = 256 << 20
PROLOGUE_SCAN_BYTES = 64 << 10


class SplRejected(Exception):
    """The document must not be used (unsafe or not an SPL document)."""


def _q(tag: str) -> str:
    return f"{{{HL7}}}{tag}"


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def _attr(elem, child: str, attr: str):
    if elem is None:
        return None
    c = elem.find(_q(child))
    return c.get(attr) if c is not None else None


def _text(elem, child: str):
    if elem is None:
        return None
    c = elem.find(_q(child))
    if c is None:
        return None
    t = "".join(c.itertext()).strip()
    return " ".join(t.split()) or None


def _first(elem, names):
    for n in names:
        c = elem.find(_q(n))
        if c is not None:
            return c, n
    return None, None


def _indexed_children(elem):
    counts: dict[str, int] = {}
    for child in elem:
        tag = _local(child.tag)
        counts[tag] = counts.get(tag, 0) + 1
        yield tag, counts[tag], child


class _GuardedReader(io.RawIOBase):
    """Hash + byte-cap the XML stream and reject DTD/entity declarations up front."""

    def __init__(self, raw, max_bytes: int):
        super().__init__()
        self._raw = raw
        self._max = max_bytes
        self.count = 0
        self.sha256 = hashlib.sha256()
        head = raw.read(PROLOGUE_SCAN_BYTES)
        if b"<!DOCTYPE" in head or b"<!ENTITY" in head:
            raise SplRejected("xml_dtd_or_entity_declaration")
        self._pending = head
        self._account(head)

    def _account(self, data: bytes):
        self.count += len(data)
        if self.count > self._max:
            raise SplRejected(f"xml_exceeds_{self._max}_bytes")
        self.sha256.update(data)

    def readable(self):
        return True

    def readinto(self, b):
        if self._pending:
            n = min(len(b), len(self._pending))
            b[:n] = self._pending[:n]
            self._pending = self._pending[n:]
            return n
        data = self._raw.read(len(b))
        self._account(data)
        b[: len(data)] = data
        return len(data)


@dataclass
class _Frame:
    tag: str
    idx: int
    elem: ET.Element
    counts: dict


def _org(org_elem, loc: str) -> dict:
    ids = [{"root": i.get("root"), "extension": i.get("extension")} for i in org_elem.findall(_q("id"))]
    addr_el = org_elem.find(_q("addr"))
    addr = None
    if addr_el is not None:
        addr = {
            "street": [" ".join("".join(s.itertext()).split()) for s in addr_el.findall(_q("streetAddressLine"))],
            "city": _text(addr_el, "city"),
            "state": _text(addr_el, "state"),
            "postal_code": _text(addr_el, "postalCode"),
            "country": _text(addr_el, "country"),
        }
    return {
        "loc": loc,
        "name": _text(org_elem, "name"),
        "ids": ids,
        "duns": [i["extension"] for i in ids if i["root"] == DUNS_ROOT and i["extension"]],
        "fei": [i["extension"] for i in ids if i["root"] == FEI_ROOT and i["extension"]],
        "address": addr,
    }


def _operation(perf_elem, loc: str) -> dict:
    act = perf_elem.find(_q("actDefinition"))
    code = act.find(_q("code")) if act is not None else None
    products = []
    if act is not None:
        for prod in act.findall(_q("product")):
            mp = prod.find(_q("manufacturedProduct"))
            kind = mp.find(_q("manufacturedMaterialKind")) if mp is not None else None
            c = kind.find(_q("code")) if kind is not None else None
            if c is not None:
                products.append({"code": c.get("code"), "code_system": c.get("codeSystem")})
    qualifiers = []
    if act is not None:
        for subj in act.findall(_q("subjectOf")):
            for q in subj:
                qc = q.find(_q("code"))
                qualifiers.append({"kind": _local(q.tag),
                                   "code": qc.get("code") if qc is not None else None,
                                   "display_name": qc.get("displayName") if qc is not None else None})
    return {
        "loc": loc,
        "code": code.get("code") if code is not None else None,
        "code_system": code.get("codeSystem") if code is not None else None,
        "display_name": code.get("displayName") if code is not None else None,
        "product_codes": products,
        "qualifiers": qualifiers,
    }


def _walk_author(author, loc: str, out: dict) -> None:
    """Recurse assignedEntity -> (represented|assigned)Organization -> assignedEntity ..."""

    def visit(entity, eloc: str, depth: int):
        org, org_tag = _first(entity, ("representedOrganization", "assignedOrganization"))
        if org is None:
            return
        oloc = f"{eloc}/{org_tag}"
        rec = _org(org, oloc)
        rec["depth"] = depth
        rec["role"] = ORG_ROLE_BY_DEPTH.get(depth, f"depth_{depth}")
        ops = [_operation(p, f"{eloc}/performance[{i}]")
               for tag, i, p in _indexed_children(entity) if tag == "performance"]
        rec["operations"] = ops
        if ops and depth != 3:
            out["anomalies"].append({"kind": "operations_outside_establishment_level", "loc": eloc})
        if depth > 3:
            out["anomalies"].append({"kind": "organization_deeper_than_establishment", "loc": oloc})
        out["organizations"].append(rec)
        for tag, i, child in _indexed_children(org):
            if tag == "assignedEntity":
                visit(child, f"{oloc}/assignedEntity[{i}]", depth + 1)

    for tag, i, ent in _indexed_children(author):
        if tag == "assignedEntity":
            visit(ent, f"{loc}/assignedEntity[{i}]", 1)


def _marketing(holder) -> list[dict]:
    acts = []
    for subj in holder.findall(_q("subjectOf")):
        ma = subj.find(_q("marketingAct"))
        if ma is None:
            continue
        et = ma.find(_q("effectiveTime"))
        acts.append({
            "code": _attr(ma, "code", "code"),
            "status": _attr(ma, "statusCode", "code"),
            "low": _attr(et, "low", "value") if et is not None else None,
            "high": _attr(et, "high", "value") if et is not None else None,
        })
    return acts


def _packages(holder, holder_loc: str, contains: str | None, level: int, out: list) -> None:
    for tag, i, ac in _indexed_children(holder):
        if tag != "asContent":
            continue
        cpp, cpp_tag = _first(ac, _PACKAGE)
        if cpp is None:
            continue
        loc = f"{holder_loc}/asContent[{i}]/{cpp_tag}"
        code = cpp.find(_q("code"))
        qty = ac.find(_q("quantity"))
        num = qty.find(_q("numerator")) if qty is not None else None
        raw = code.get("code") if code is not None else None
        out.append({
            "loc": loc,
            "package_ndc_raw": raw,
            "code_system": code.get("codeSystem") if code is not None else None,
            "form": _attr(cpp, "formCode", "displayName"),
            "level": level,
            "contains": contains,
            "quantity": {"value": num.get("value"), "unit": num.get("unit")} if num is not None else None,
            "marketing": _marketing(ac),
        })
        _packages(cpp, loc, raw, level + 1, out)


def _product(outer, loc: str, section_code: str | None) -> dict:
    inner, inner_tag = _first(outer, _PRODUCT_INNER)
    ploc = f"{loc}/{inner_tag}" if inner is not None else loc
    code = inner.find(_q("code")) if inner is not None else None
    raw = code.get("code") if code is not None else None
    generic = None
    if inner is not None:
        g = inner.find(_q("asEntityWithGeneric"))
        if g is not None:
            generic = _text(g.find(_q("genericMedicine")), "name")
    routes = []
    for ci in outer.findall(_q("consumedIn")):
        sa = ci.find(_q("substanceAdministration"))
        rc = sa.find(_q("routeCode")) if sa is not None else None
        if rc is not None:
            routes.append({"code": rc.get("code"), "display_name": rc.get("displayName")})
    approvals = []
    for subj in outer.findall(_q("subjectOf")):
        ap = subj.find(_q("approval"))
        if ap is not None:
            approvals.append({"id": _attr(ap, "id", "extension"),
                              "category_code": _attr(ap, "code", "code"),
                              "category": _attr(ap, "code", "displayName")})
    packages: list = []
    parts = []
    if inner is not None:
        _packages(inner, ploc, raw, 1, packages)
        for tag, i, part in _indexed_children(inner):
            if tag != "part":
                continue
            pp, pp_tag = _first(part, ("partProduct", "partMedicine"))
            if pp is None:
                continue
            pploc = f"{ploc}/part[{i}]/{pp_tag}"
            pcode = pp.find(_q("code"))
            ppk: list = []
            _packages(pp, pploc, pcode.get("code") if pcode is not None else None, 1, ppk)
            parts.append({"loc": pploc, "code": pcode.get("code") if pcode is not None else None,
                          "code_system": pcode.get("codeSystem") if pcode is not None else None,
                          "name": _text(pp, "name"), "form": _attr(pp, "formCode", "displayName"),
                          "packages": ppk})
    return {
        "loc": ploc,
        "section_code": section_code,
        "product_ndc_raw": raw,
        "code_system": code.get("codeSystem") if code is not None else None,
        "name": _text(inner, "name"),
        "generic_name": generic,
        "form": _attr(inner, "formCode", "displayName"),
        "routes": routes,
        "approvals": approvals,
        "marketing": _marketing(outer),
        "packages": packages,
        "parts": parts,
    }


def parse_spl(stream, *, max_bytes: int = DEFAULT_MAX_XML_BYTES) -> dict:
    """Parse one SPL XML stream. Raises SplRejected / ET.ParseError on unusable input."""
    src = _GuardedReader(stream, max_bytes)
    doc = {
        "document_id": None, "document_type_code": None, "document_type": None,
        "set_id": None, "version": None, "effective_time": None,
        "organizations": [], "products": [], "anomalies": [],
    }
    stack: list[_Frame] = []
    root_seen = False
    for event, elem in ET.iterparse(io.BufferedReader(src, 1 << 16), events=("start", "end")):
        if event == "start":
            tag = _local(elem.tag)
            if not stack:
                if elem.tag != _q("document"):
                    raise SplRejected(f"root_is_not_hl7_document:{elem.tag}")
                root_seen = True
                stack.append(_Frame(tag, 1, elem, {}))
                continue
            parent = stack[-1]
            parent.counts[tag] = parent.counts.get(tag, 0) + 1
            stack.append(_Frame(tag, parent.counts[tag], elem, {}))
            continue

        frame = stack[-1]
        depth = len(stack)
        if depth == 2:
            if frame.tag == "id":
                doc["document_id"] = elem.get("root")
            elif frame.tag == "code":
                doc["document_type_code"] = elem.get("code")
                doc["document_type"] = elem.get("displayName")
            elif frame.tag == "effectiveTime":
                doc["effective_time"] = elem.get("value")
            elif frame.tag == "setId":
                doc["set_id"] = elem.get("root")
            elif frame.tag == "versionNumber":
                doc["version"] = elem.get("value")
            elif frame.tag == "author":
                _walk_author(elem, f"/document/author[{frame.idx}]", doc)
                elem.clear()
        elif frame.tag == "subject" and depth >= 2 and stack[-2].tag == "section":
            outer = elem.find(_q("manufacturedProduct"))
            if outer is not None:
                loc = "/document/" + "/".join(f"{f.tag}[{f.idx}]" for f in stack[1:]) + "/manufacturedProduct"
                section_code = _attr(stack[-2].elem, "code", "code")
                doc["products"].append(_product(outer, loc, section_code))
            elem.clear()
        elif frame.tag == "section":
            elem.clear()
        elif frame.tag == "performance" and stack[1].tag != "author":
            # Guard against a blind spot: operations we would otherwise never see.
            doc["anomalies"].append({"kind": "performance_outside_author",
                                     "loc": "/document/" + "/".join(f"{f.tag}[{f.idx}]" for f in stack[1:])})
        stack.pop()
    if not root_seen:
        raise SplRejected("empty_document")
    doc["xml_bytes"] = src.count
    doc["xml_sha256"] = src.sha256.hexdigest()
    for p in doc["products"]:
        if p["section_code"] != PRODUCT_DATA_SECTION:
            doc["anomalies"].append({"kind": "product_outside_product_data_section", "loc": p["loc"]})
    return doc


def establishments(doc: dict) -> list[dict]:
    return [o for o in doc["organizations"] if o["role"] == "establishment"]


def labelers(doc: dict) -> list[dict]:
    return [o for o in doc["organizations"] if o["role"] == "labeler"]


def operation_edges(doc: dict) -> list[dict]:
    """Flatten to (product code, establishment DUNS, operation) edges with citations.

    One edge per (operation element, product code). An establishment with no DUNS
    yields duns=None, which downstream must treat as UNKNOWN identity.
    """
    edges = []
    for est in establishments(doc):
        duns_list = est["duns"] or [None]
        for op in est["operations"]:
            codes = op["product_codes"] or [{"code": None, "code_system": None}]
            for pc in codes:
                for duns in duns_list:
                    edges.append({
                        "set_id": doc["set_id"], "version": doc["version"],
                        "product_code": pc["code"], "product_code_system": pc["code_system"],
                        "duns": duns, "establishment_name": est["name"],
                        "operation_code": op["code"], "operation": op["display_name"],
                        "loc": op["loc"],
                    })
    return edges

"""DST-08 research prototype: source-NDC references and source-linked manufacturing evidence (fineprint.lineage).

Pure-rule tests run everywhere. The database tests build a synthetic release in FINEPRINT_TEST_DB with one scenario
per rule (a resolved and consistent source; no candidate; several candidates; a package code; a code only in a
non-canonical version; a multi-hop chain; a cycle; dosage-form and strength conflicts; a repackager asserting
MANUFACTURE; a kit part; a source without DIRECT evidence; a wrong equivalence code; two sources on one product; a
self reference), build the graph and the lineage schema, and check every classification, that the national tables
and DIRECT edges are untouched, that a rebuild is identical, and that the SQL rule equals the Python rule.

Rule v2 has one scenario per class of the version-aware check (drift resolved, with and without site continuity; a
confirmed conflict; notation only; several presentations; no history; a match with an earlier version only; a
characteristic not stated at the applicable version; a source set newer than the citing label), with archived source
versions in a temporary cache and a manifest like the fetch script's.
"""

import io
import json
import os
import shutil
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from tests import release_builder as rb
from tests import spl_factory as sf

from fineprint import lineage, spl

try:
    from fineprint import db, graph, identity, ingest
except ImportError:
    db = None

TEST_DB = os.environ.get("FINEPRINT_TEST_DB", "fineprint_test")
X, Z, GHOST = "500000001", "500000002", "500000009"      # source maker (registered), repackager (registered), unregistered
NCI, NDCS = lineage.NCI_SYSTEM, lineage.NDC_SYSTEM
TABLET, CAPSULE, KIT = "C42998", "C25158", "C47916"
A10 = [("UNIIAAAAAA", "10", "mg")]


def available():
    if db is None:
        return False
    try:
        db.connect(TEST_DB, connect_timeout=3).close()
        return True
    except Exception:
        return False


def equiv(src, *, eq="C64637", eq_system=NCI, src_system=NDCS):
    return (f'<asEquivalentEntity classCode="EQUIV"><code code="{eq}" codeSystem="{eq_system}"/>'
            f'<definingMaterialKind><code code="{src}" codeSystem="{src_system}"/></definingMaterialKind></asEquivalentEntity>')


def product_xml(code, *, form=TABLET, active=A10, sources=(), parts=(), tag="manufacturedProduct", denominator="1"):
    ing = "".join(f'<ingredient classCode="ACTIB"><quantity><numerator value="{v}" unit="{u}"/>'
                  f'<denominator value="{denominator}" unit="1"/>'
                  f'</quantity><ingredientSubstance><code code="{unii}" codeSystem="2.16.840.1.113883.4.9"/><name>S</name>'
                  f'</ingredientSubstance></ingredient>' for unii, v, u in active)
    pk = (f'<asContent><quantity><numerator value="30" unit="1"/><denominator value="1" unit="1"/></quantity>'
          f'<containerPackagedProduct><code code="{code}-1" codeSystem="{NDCS}"/><formCode displayName="BOTTLE"/>'
          f'</containerPackagedProduct></asContent>')
    pt = "".join(f'<part><quantity><numerator value="1" unit="1"/><denominator value="1" unit="1"/></quantity><partProduct>'
                 f'<code code="{p["code"]}" codeSystem="{NDCS}"/><name>part</name><formCode code="{p.get("form", TABLET)}"/>'
                 + "".join(equiv(s) for s in p.get("sources", ())) + "</partProduct></part>" for p in parts)
    return (f'<{tag}><code code="{code}" codeSystem="{NDCS}"/><name>Drug {code}</name>'
            f'<formCode code="{form}" codeSystem="{NCI}" displayName="F"/>{ing}{pk}{"".join(sources)}{pt}</{tag}>')


def doc_xml(set_id, version, products, establishments, labeler="111111111"):
    ests = ""
    for duns, ops in establishments:
        perf = "".join(f'<performance><actDefinition><code code="{op}" displayName="{name}"/>'
                       + "".join(f'<product><manufacturedProduct><manufacturedMaterialKind><code code="{c}" '
                                 f'codeSystem="{NDCS}"/></manufacturedMaterialKind></manufacturedProduct></product>' for c in codes)
                       + "</actDefinition></performance>" for op, name, codes in ops)
        ests += (f'<assignedEntity><assignedOrganization><id root="{spl.DUNS_ROOT}" extension="{duns}"/><name>E{duns}</name>'
                 f'</assignedOrganization>{perf}</assignedEntity>')
    subj = "".join(f"<subject><manufacturedProduct>{p}</manufacturedProduct></subject>" for p in products)
    return (f'<?xml version="1.0" encoding="UTF-8"?>\n<document xmlns="urn:hl7-org:v3"><id root="doc-{set_id}-{version}"/>'
            f'<code code="34391-3" displayName="HUMAN PRESCRIPTION DRUG LABEL"/><effectiveTime value="20260101"/>'
            f'<setId root="{set_id}"/><versionNumber value="{version}"/><author><assignedEntity><representedOrganization>'
            f'<id root="{spl.DUNS_ROOT}" extension="{labeler}"/><name>Labeler</name><assignedEntity><assignedOrganization>'
            f'{ests}</assignedOrganization></assignedEntity></representedOrganization></assignedEntity></author>'
            f'<component><structuredBody><component><section><code code="48780-1"/>{subj}</section></component>'
            f'</structuredBody></component></document>').encode()


MFG, REPACK = ("C43360", "MANUFACTURE"), ("C73606", "REPACK")


def sid(n):
    return f"00000000-0000-4000-8000-0000000008{n:02d}"


# key -> (set number, product code); the repackaged products are each in their own set (lineage needs other sets).
R = {k: (i, f"44444-00{i:02d}") for i, k in enumerate(
    ["ok", "none", "multi", "package", "hop", "cyc_a", "cyc_b", "form", "strength", "claims", "kit", "nodirect",
     "noncanon", "equiv", "two", "self", "decimal", "ratio"], 1)}


def chars(imprint=None, color=None):
    """Physical characteristics on the manufacturedProduct role (appended after the product element)."""
    def ch(code, value):
        return (f'<subjectOf><characteristic classCode="OBS"><code code="{code}" codeSystem="2.16.840.1.113883.1.11.19255"/>'
                f'{value}</characteristic></subjectOf>')
    return ((ch("SPLIMPRINT", f"<value>{imprint}</value>") if imprint else "")
            + (ch("SPLCOLOR", f'<value code="{color}" codeSystem="{NCI}"/>') if color else ""))


# Rule v2 scenarios: key -> (citing imprint, citing colour, source versions [(version, DailyMed date, presentations of
# the cited code [(imprint, colour)], MANUFACTURE DUNS)]). The last version is the release's canonical one; the others
# exist only in the archive cache. Every citing label version was published on D.
OTHER = "500000003"
D = "2021-06-01"
V2 = {
    "drift": ("OLD1", None, [(1, "2020-01-01", [("OLD1", None)], X), (2, "2022-01-01", [("NEW1", None)], X),
                             (3, "2023-01-01", [("NEW1", None)], X)]),
    "sitechg": ("OLD2", None, [(1, "2020-01-01", [("OLD2", None)], OTHER), (2, "2023-01-01", [("NEW2", None)], X)]),
    "conflict": ("ZZZ", None, [(1, "2020-01-01", [("AAA", None)], X), (2, "2023-01-01", [("AAA", None)], X)]),
    "notation": ("RX692", None, [(1, "2020-01-01", [("RX692;RX692", None)], X)]),
    "several": ("P1", None, [(1, "2020-01-01", [("P1", None), ("P2", None)], X), (2, "2023-01-01", [("P2", None)], X)]),
    "nohist": ("QQ2", None, [(1, "2020-01-01", [("QQ1", None)], X)]),
    "earlier": ("OLD7", None, [(1, "2019-01-01", [("OLD7", None)], X), (2, "2020-01-01", [("MID7", None)], X),
                               (3, "2023-01-01", [("NEW7", None)], X)]),
    "unstated": ("OLD8", "C48325", [(1, "2020-01-01", [(None, "C48325")], X), (2, "2023-01-01", [("NEW8", "C48325")], X)]),
    "postdates": ("S0", None, [(1, "2023-01-01", [("S9", None)], X)]),
    "agree": ("OK1", None, [(1, "2020-01-01", [("OK1", None)], X)]),
    # the applicable version names no establishment at all (DUNS None): no site continuity, but not a change of sites
    "nosite": ("OLD9", None, [(1, "2020-01-01", [("OLD9", None)], None), (2, "2023-01-01", [("NEW9", None)], X)]),
}


def v2_citing(key):
    n = 20 + list(V2).index(key)
    return sid(n), f"44444-00{n:02d}"


def v2_source(key):
    n = 70 + list(V2).index(key)
    return sid(n), f"33333-00{n:02d}"


def v2_source_xml(key, version):
    s, code = v2_source(key)
    _, _, presentations, duns = next(h for h in V2[key][2] if h[0] == version)
    return doc_xml(s, version, [product_xml(code) + chars(i, c) for i, c in presentations],
                   [(duns, [(*MFG, [code])])] if duns else [], labeler="333333333")


def v2_documents():
    out = []
    for key, (imprint, color, versions) in V2.items():
        s, code = v2_citing(key)
        out.append((s, 1, doc_xml(s, 1, [product_xml(code, sources=[equiv(v2_source(key)[1])]) + chars(imprint, color)],
                                  [(Z, [(*REPACK, [code])])], labeler="444444444")))
        canonical = versions[-1][0]
        out.append((v2_source(key)[0], canonical, v2_source_xml(key, canonical)))
    return out


def write_history(root: Path):
    """The archive cache and the manifest validate_v2 reads, as dst08_fetch_source_versions.py would write them."""
    cache, history, docs = root / "history", {}, []
    for key, (_, _, versions) in V2.items():
        history[v2_citing(key)[0]] = {"status": "ok", "versions": [{"version": 1, "published_at": D}]}
        s = v2_source(key)[0]
        if key == "nohist":
            history[s] = {"status": "unavailable", "versions": []}
            continue
        history[s] = {"status": "ok", "versions": [{"version": v, "published_at": p} for v, p, _, _ in versions]}
        for v, _, _, _ in versions:
            xml = v2_source_xml(key, v)
            z = sf.nested(xml)
            path = cache / "spl" / f"{s}_v{v}.zip"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(z)
            docs.append({"set_id": s, "version": v, "status": "ok", "url": f"https://example.invalid/{s}/{v}",
                         "retrieved_at": "2026-10-25T00:00:00Z", "zip_path": f"spl/{s}_v{v}.zip",
                         "zip_sha256": rb.sha256(z), "xml_member": "doc.xml", "xml_sha256": rb.sha256(xml),
                         "document_id": f"doc-{s}-{v}", "effective_time": "20260101"})
    manifest = root / "source_history_manifest.json"
    manifest.write_text(json.dumps({"history": history, "documents": docs}), encoding="utf-8")
    return manifest, cache


def documents():
    src = lambda n, code, duns, **kw: (sid(50 + n), 1, doc_xml(sid(50 + n), 1, [product_xml(code, **kw)],  # noqa: E731
                                                               [(duns, [(*MFG, [code])])], labeler="333333333"))
    docs = [
        src(1, "33333-0001", X),                                   # the source: DIRECT
        src(2, "33333-0002", GHOST, active=[("UNIIBBBBBB", "5", "mg")]),   # source with UNKNOWN_SITE only
        src(3, "33333-0003", X), src(4, "33333-0003", X),          # the same product code in two sets
        # set 55, two versions: v1 lists 0005 and 0006, the canonical v2 only 0006
        (sid(55), 1, doc_xml(sid(55), 1, [product_xml("33333-0005"), product_xml("33333-0006")],
                              [(X, [(*MFG, ["33333-0005", "33333-0006"])])], labeler="333333333")),
        (sid(55), 2, doc_xml(sid(55), 2, [product_xml("33333-0006")], [(X, [(*MFG, ["33333-0006"])])], labeler="333333333")),
    ]

    def rep(key, *, sources=(), mfg=False, **kw):
        n, code = R[key]
        ops = [(*REPACK, [code])] + ([(*MFG, [code])] if mfg else [])
        return (sid(n), 1, doc_xml(sid(n), 1, [product_xml(code, sources=sources, **kw)], [(Z, ops)], labeler="444444444"))

    docs += [
        rep("ok", sources=[equiv("33333-0001")]),
        rep("none", sources=[equiv("33333-0099")]),
        rep("multi", sources=[equiv("33333-0003")]),
        rep("package", sources=[equiv("33333-0001-1")]),       # 5-4-1: a package code whose prefix is a real source
        rep("hop", sources=[equiv(R["ok"][1])]),
        rep("cyc_a", sources=[equiv(R["cyc_b"][1])]),
        rep("cyc_b", sources=[equiv(R["cyc_a"][1])]),
        rep("form", sources=[equiv("33333-0001")], form=CAPSULE),
        rep("strength", sources=[equiv("33333-0001")], active=[("UNIIAAAAAA", "20", "mg")]),
        rep("claims", sources=[equiv("33333-0001")], mfg=True),
        rep("kit", form=KIT, active=[], parts=[{"code": "44444-0099", "sources": ["33333-0001"]}]),
        rep("nodirect", sources=[equiv("33333-0002")], active=[("UNIIBBBBBB", "5", "mg")]),
        rep("noncanon", sources=[equiv("33333-0005")]),
        rep("equiv", sources=[equiv("33333-0001", eq="C99999")]),
        rep("two", sources=[equiv("33333-0001"), equiv("33333-0006")]),
        rep("self", sources=[equiv(R["self"][1])]),
        # the same strength spelled differently (seen in the DST-08 sample: '.25' against '0.25', '1.0' against '1')
        rep("decimal", sources=[equiv("33333-0001")], active=[("UNIIAAAAAA", "10.0", "mg")]),
        # an equal ratio stated with a different denominator is still a difference, not a tolerance
        rep("ratio", sources=[equiv("33333-0001")], active=[("UNIIAAAAAA", "20", "mg")], denominator="2"),
    ]
    return docs + v2_documents()


def build_fixture(root: Path):
    members = [(f"prescription/2026010{v}_{s}.zip", sf.nested(x)) for s, v, x in documents()]
    manifest = rb.write_manifest(root, {"lineage_part.zip": members})
    cur = sf.decrs_text([
        {"FEI_NUMBER": "3500000001", "DUNS_NUMBER": X, "FIRM_NAME": "Maker", "ADDRESS": "1 Plant Rd", "EXPIRATION_DATE": "12/31/2026"},
        {"FEI_NUMBER": "3500000002", "DUNS_NUMBER": Z, "FIRM_NAME": "Repacker", "ADDRESS": "2 Repack Rd", "EXPIRATION_DATE": "12/31/2026"}])
    regs = [("fda_decrs_registration", root / "cur" / "drls_reg.zip", "drls_reg.txt", cur),
            ("fda_decrs_excluded", root / "cur" / "drls_excluded.zip", "drls_excluded.txt", sf.decrs_text([]))]
    with db.connect(TEST_DB, autocommit=True) as c:
        db.reset_national(c)
        c.execute("DROP SCHEMA IF EXISTS lineage CASCADE")
        db.migrate(c)
        inputs = ingest.release_inputs(manifest)
        run_id = ingest.start_run(c, {"test": "source_lineage"})
        p = inputs["parts"][0]
        psid, _ = ingest.register_source(c, kind="dailymed_human_rx_full_part", advertised=p["advertised"],
                                         record=p["record"], path=p["path"], release_label="2026-10-16", verify=False)
        ingest.ingest_part(c, source_file_id=psid, path=p["path"], run_id=run_id, log=lambda m: None)
        ingest.refresh_operation_types(c, run_id)
        ingest.finish_run(c, run_id, "completed", {})
        for kind, path, member, text in regs:
            rec = sf.write_zip_text(path, member, text)
            rows, info = identity.parse_decrs(path)
            fsid, _ = identity.register_file(c, kind=kind, path=path, record=rec, release_label=info["generated_at"][:10],
                                             generated_at=info["generated_at"])
            identity.load_rows(c, fsid, rows)
        graph.build(c, log=lambda m: None)


class PureRules(unittest.TestCase):
    def validity(self, **kw):
        base = dict(class_code="EQUIV", eq_code="C64637", eq_system=NCI, src_code="12345-678", src_system=NDCS,
                    own_code="55555-1234", n_on_product=1)
        return lineage.reference_validity(**{**base, **kw})

    def test_validity_follows_the_implementation_guide_form(self):
        self.assertEqual(self.validity(), "VALID")
        self.assertEqual(self.validity(class_code=None), "VALID")
        self.assertEqual(self.validity(class_code="SAME"), "NOT_EQUIV_CLASS")
        self.assertEqual(self.validity(eq_code="C99999"), "NOT_SAME_EQUIVALENCE")
        self.assertEqual(self.validity(eq_system="2.16.840.1.113883.3.2964"), "NOT_SAME_EQUIVALENCE")
        self.assertEqual(self.validity(src_system="1.3.160"), "NOT_NDC_CODE_SYSTEM")
        self.assertEqual(self.validity(src_code="12345-678-90"), "PACKAGE_CODE_NOT_PRODUCT_CODE")
        self.assertEqual(self.validity(src_code="12345678"), "MALFORMED_OR_MISSING_CODE")
        self.assertEqual(self.validity(src_code=None), "MALFORMED_OR_MISSING_CODE")
        self.assertEqual(self.validity(src_code="55555-1234"), "SELF_REFERENCE")
        self.assertEqual(self.validity(n_on_product=2), "MULTIPLE_SOURCES_FOR_PRODUCT")

    def test_a_package_code_is_never_truncated_to_a_product_code(self):
        self.assertEqual(lineage.code_pattern("0409-3308-03"), "package")
        self.assertEqual(lineage.code_pattern("0409-3308"), "product")
        self.assertEqual(self.validity(src_code="0409-3308-03"), "PACKAGE_CODE_NOT_PRODUCT_CODE")

    def test_eligibility_needs_every_condition(self):
        ok = dict(validity="VALID", product_kind="product", resolution="RESOLVED", selection_class="confirmed",
                  chain="SINGLE_HOP", consistency="CONSISTENT", source_repackaged=False, source_has_direct=True)
        self.assertEqual(lineage.eligibility(**ok), ("ELIGIBLE", []))
        for change, reason in ((dict(validity="PACKAGE_CODE_NOT_PRODUCT_CODE"), "validity:PACKAGE_CODE_NOT_PRODUCT_CODE"),
                               (dict(product_kind="kit_part"), "citing:kit_part"),
                               (dict(resolution="MULTIPLE_CANDIDATES"), "resolution:MULTIPLE_CANDIDATES"),
                               (dict(selection_class="ambiguous"), "source_version:ambiguous"),
                               (dict(chain="CYCLE"), "chain:CYCLE"),
                               (dict(source_repackaged=True), "source:repackaged_or_relabeled"),
                               (dict(consistency="FORM_DIFFERS"), "consistency:FORM_DIFFERS"),
                               (dict(source_has_direct=False), "source:no_direct_manufacture")):
            status, reasons = lineage.eligibility(**{**ok, **change})
            self.assertEqual(status, "EXCLUDED", change)
            self.assertIn(reason, reasons, change)

    def test_extracted_locations_are_the_parsers(self):
        xml = doc_xml(sid(1), 1, [product_xml("44444-0001", sources=[equiv("33333-0001")]),
                                  product_xml("44444-0011", parts=[{"code": "44444-0099", "sources": ["33333-0001"]}])],
                      [(Z, [(*REPACK, ["44444-0001"])])])
        parsed = spl.parse_spl(io.BytesIO(xml))
        locs = sorted([p["loc"] for p in parsed["products"]] + [q["loc"] for p in parsed["products"] for q in p["parts"]])
        found = lineage.extract(xml)
        self.assertEqual(sorted(p["loc"] for p in found), locs)
        refs = [(p["kind"], r["src_code"], r["loc"]) for p in found for r in p["refs"]]
        self.assertEqual(sorted(r[:2] for r in refs), [("kit_part", "33333-0001"), ("product", "33333-0001")])
        self.assertTrue(all(r[2].endswith("/asEquivalentEntity[1]") for r in refs))

    def test_xml_with_entity_declarations_is_refused(self):
        with self.assertRaises(ValueError):
            lineage.extract(b'<?xml version="1.0"?><!DOCTYPE x [<!ENTITY e "x">]><document/>')

    def test_the_build_refuses_the_production_database(self):
        class Conn:
            def execute(self, sql, *a):
                class R:
                    def fetchone(self):
                        return ("fineprint",)
                return R()
        with self.assertRaises(lineage.LineageRefused):
            lineage.build(Conn())

    def test_characteristics_are_read_from_the_product_role(self):
        xml = doc_xml(sid(1), 1, [product_xml("44444-0001") + chars("m 30", "C48325")], [(Z, [(*REPACK, ["44444-0001"])])])
        (p,) = lineage.extract(xml)
        self.assertEqual(p["characteristics"], {"imprint": ["M30"], "imprint_raw": ["m 30"], "imprint_tokens": ["30", "M"],
                                                "color": ["C48325"]})

    def test_physical_comparison_keeps_the_diagnostics_strict_test_and_adds_v2_values(self):
        def c(*imprints, color=None):
            return lineage.characteristics(ET.fromstring(
                f'<r xmlns="urn:hl7-org:v3">{"".join(chars(i) for i in imprints)}{chars(color=color)}</r>'))
        marks = lineage.physical_compare(c("RX692"), c("RX692;RX692"))
        self.assertEqual((marks["outcome"], marks["per"]["imprint"]), ("IMPRINT_DIFFERS", "SAME_MARKS"))
        several = lineage.physical_compare(c("P1"), c("P1", "P2"))
        self.assertEqual((several["outcome"], several["per"]["imprint"]), ("IMPRINT_DIFFERS", "ONE_OF_SEVERAL"))
        other = lineage.physical_compare(c("A1", color="C48325"), c("A1", color="C48330"))
        self.assertEqual((other["outcome"], other["differing"], other["per"]),
                         ("IMPRINT_EQUAL_OTHER_DIFFERS", ["color"], {"imprint": "SAME", "color": "DIFFERS"}))
        self.assertEqual(lineage.physical_compare(c("A1"), c(color="C48325"))["outcome"], "NOTHING_COMPARABLE")

    def test_version_aware_classes_follow_the_preregistered_order(self):
        def cls(failure=None, at=None, now=None, matching=(), unretrievable=(), conflicting=("imprint",)):
            return lineage.classify_version_aware(failure=failure, conflicting=list(conflicting), at_applicable=at or {},
                                                  at_current=now or {"imprint": "DIFFERS"},
                                                  versions_matching=list(matching),
                                                  versions_unretrievable=list(unretrievable))[0]
        self.assertEqual(cls("history_unavailable"), "MISSING_COMPARISON_EVIDENCE")
        self.assertEqual(cls("applicable_version_not_retrievable"), "MISSING_COMPARISON_EVIDENCE")
        self.assertEqual(cls("source_set_not_published_by_citing_date"), "UNRESOLVED_AMBIGUITY")
        self.assertEqual(cls("code_not_in_applicable_version"), "UNRESOLVED_AMBIGUITY")
        self.assertEqual(cls(at={"imprint": "DIFFERS"}), "CONFIRMED_CONFLICT")
        self.assertEqual(cls(at={"imprint": "DIFFERS"}, matching=[1]), "UNRESOLVED_AMBIGUITY")
        self.assertEqual(cls(at={"imprint": "DIFFERS"}, unretrievable=[4]), "UNRESOLVED_AMBIGUITY")
        # a difference at the applicable version wins over a missing field, which wins over several presentations
        self.assertEqual(cls(at={"color": "DIFFERS", "imprint": "ONE_SIDE"}), "CONFIRMED_CONFLICT")
        self.assertEqual(cls(at={"imprint": "ONE_SIDE"}), "MISSING_COMPARISON_EVIDENCE")
        self.assertEqual(cls(at={"imprint": "SAME", "color": "ONE_OF_SEVERAL"}, conflicting=("imprint", "size")),
                         "MISSING_COMPARISON_EVIDENCE")
        self.assertEqual(cls(at={"imprint": "ONE_OF_SEVERAL"}), "MULTIPLE_VALID_PRESENTATIONS")
        self.assertEqual(cls(at={"imprint": "SAME"}), "VERSION_DRIFT_RESOLVED")
        self.assertEqual(cls(at={"imprint": "SAME_MARKS"}, now={"imprint": "SAME_MARKS"}), "NOTATION_ONLY")


@unittest.skipUnless(available(), f"PostgreSQL test database {TEST_DB!r} not reachable")
class LineageDb(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        assert TEST_DB != "fineprint", "refusing to run destructive tests on the main database"
        cls.tmp = tempfile.TemporaryDirectory()
        build_fixture(Path(cls.tmp.name))
        cls.conn = db.connect(TEST_DB, autocommit=True)
        cls.before = (db.fingerprint(cls.conn), cls.edges(), cls.statuses())
        cls.first = lineage.build(cls.conn, log=lambda m: None)

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()
        cls.tmp.cleanup()

    @classmethod
    def edges(cls):
        return cls.conn.execute("SELECT assertion_pk, operation_code, duns, confidence, confidence_reasons "
                                "FROM national.operation_edge ORDER BY 1").fetchall()

    @classmethod
    def statuses(cls):
        return cls.conn.execute("SELECT product_pk, manufacturing_status, evidence_status FROM "
                                "national.v_product_manufacturing_status ORDER BY 1").fetchall()

    def row(self, key):
        code = R[key][1] if key in R else key
        rows = self.conn.execute(
            """SELECT r.validity, x.resolution, x.chain, x.consistency, x.status, x.reasons, x.source_set_id
               FROM lineage.source_reference r JOIN lineage.source_resolution x USING (reference_pk)
               WHERE r.product_ndc_raw = %s ORDER BY r.loc""", (code,)).fetchall()
        self.assertTrue(rows, key)
        return rows

    def tier(self, code):
        return self.conn.execute("SELECT direct_tier_status, coverage_tier FROM lineage.v_product_coverage "
                                 "WHERE ndc_raw = %s", (code,)).fetchone()

    def test_a_resolved_consistent_source_with_direct_evidence_is_source_linked(self):
        v, res, chain, cons, status, reasons, src = self.row("ok")[0]
        self.assertEqual((v, res, chain, cons, status, list(reasons), src), ("VALID", "RESOLVED", "SINGLE_HOP", "CONSISTENT",
                                                                             "ELIGIBLE", [], sid(51)))
        self.assertEqual(self.tier(R["ok"][1]), ("NO_MANUFACTURE_EVIDENCE", "SOURCE_LINKED"))
        ev = self.conn.execute(
            """SELECT e.duns, e.fei, oe.confidence, oe.product_ndc_raw, e.registration_pk IS NOT NULL,
                      e.citing_document_pk <> e.source_document_pk
               FROM lineage.source_linked_evidence e JOIN national.operation_edge oe ON oe.assertion_pk = e.source_assertion_pk
               JOIN national.product p ON p.product_pk = e.linked_product_pk WHERE p.ndc_raw = %s""", (R["ok"][1],)).fetchall()
        self.assertEqual(ev, [(X, "3500000001", "DIRECT", "33333-0001", True, True)])

    def test_every_unsafe_or_unresolved_reference_is_excluded_with_its_reason(self):
        expect = {
            "none": ("VALID", "NO_CANDIDATE", "resolution:NO_CANDIDATE"),
            "multi": ("VALID", "MULTIPLE_CANDIDATES", "resolution:MULTIPLE_CANDIDATES"),
            "package": ("PACKAGE_CODE_NOT_PRODUCT_CODE", "NOT_RESOLVED_INVALID", "validity:PACKAGE_CODE_NOT_PRODUCT_CODE"),
            "hop": ("VALID", "RESOLVED", "chain:MULTI_HOP"),
            "cyc_a": ("VALID", "RESOLVED", "chain:CYCLE"),
            "cyc_b": ("VALID", "RESOLVED", "chain:CYCLE"),
            "form": ("VALID", "RESOLVED", "consistency:FORM_DIFFERS"),
            "strength": ("VALID", "RESOLVED", "consistency:ACTIVE_DIFFERS"),
            "ratio": ("VALID", "RESOLVED", "consistency:ACTIVE_DIFFERS"),
            "nodirect": ("VALID", "RESOLVED", "source:no_direct_manufacture"),
            "noncanon": ("VALID", "ONLY_NON_CANONICAL_VERSION", "resolution:ONLY_NON_CANONICAL_VERSION"),
            "equiv": ("NOT_SAME_EQUIVALENCE", "NOT_RESOLVED_INVALID", "validity:NOT_SAME_EQUIVALENCE"),
            "self": ("SELF_REFERENCE", "NOT_RESOLVED_INVALID", "validity:SELF_REFERENCE"),
        }
        for key, (v, res, reason) in expect.items():
            got = self.row(key)
            self.assertEqual(len(got), 1, key)
            self.assertEqual((got[0][0], got[0][1], got[0][4]), (v, res, "EXCLUDED"), key)
            self.assertIn(reason, list(got[0][5]), key)
            self.assertNotEqual(self.tier(R[key][1])[1], "SOURCE_LINKED", key)
        two = self.row("two")
        self.assertEqual([(r[0], r[4]) for r in two], [("MULTIPLE_SOURCES_FOR_PRODUCT", "EXCLUDED")] * 2)

    def test_the_same_strength_spelled_differently_is_consistent(self):
        v, res, chain, cons, status, reasons, src = self.row("decimal")[0]
        self.assertEqual((cons, status, list(reasons)), ("CONSISTENT", "ELIGIBLE", []))
        self.assertEqual([lineage.decimal_text(s) for s in (".25", "0.250", "1.0", "100", "5.0E1", "abc", "")],
                         ["0.25", "0.25", "1", "100", "50", "abc", ""])

    def test_a_kit_part_reference_is_recorded_but_never_coverage(self):
        rows = self.conn.execute("SELECT r.product_kind, x.status, x.reasons FROM lineage.source_reference r "
                                 "JOIN lineage.source_resolution x USING (reference_pk) WHERE r.product_ndc_raw = '44444-0099'").fetchall()
        self.assertEqual([(k, s) for k, s, _ in rows], [("kit_part", "EXCLUDED")])
        self.assertIn("citing:kit_part", list(rows[0][2]))
        self.assertNotEqual(self.tier(R["kit"][1])[1], "SOURCE_LINKED")

    def test_a_repackager_claiming_manufacture_stays_direct_and_its_reference_stays_separate(self):
        self.assertEqual(self.tier(R["claims"][1]), ("DIRECT", "DIRECT"))
        status = self.row("claims")[0][4]
        self.assertEqual(status, "ELIGIBLE")       # the relationship is recorded; coverage keeps DIRECT first

    def test_direct_classifications_and_national_tables_are_unchanged(self):
        self.assertEqual((db.fingerprint(self.conn), self.edges(), self.statuses()), self.before)
        tiers = dict(self.conn.execute("SELECT direct_tier_status, count(*) FROM lineage.v_product_coverage GROUP BY 1").fetchall())
        self.assertEqual(tiers, dict(self.conn.execute("SELECT manufacturing_status, count(*) FROM "
                                                       "national.v_product_manufacturing_status GROUP BY 1").fetchall()))
        direct = self.conn.execute("SELECT count(*) FROM lineage.v_product_coverage WHERE coverage_tier = 'DIRECT'").fetchone()[0]
        self.assertEqual(direct, tiers.get("DIRECT"))

    def test_a_rebuild_is_identical(self):
        again = lineage.build(self.conn, log=lambda m: None)
        self.assertEqual(again["fingerprint"], self.first["fingerprint"])
        self.assertEqual({k: v for k, v in again.items() if k != "seconds"}, {k: v for k, v in self.first.items() if k != "seconds"})

    def test_the_sql_rule_equals_the_python_rule(self):
        rows = self.conn.execute(
            """SELECT r.validity, r.product_kind, x.resolution, x.source_selection_class, x.chain, x.consistency,
                      coalesce(x.source_cites_source, false), coalesce(x.source_has_direct, false), x.status, x.reasons
               FROM lineage.source_reference r JOIN lineage.source_resolution x USING (reference_pk)""").fetchall()
        self.assertGreater(len(rows), 15)
        for v, kind, res, sel, chain, cons, rep, direct, status, reasons in rows:
            self.assertEqual(lineage.eligibility(validity=v, product_kind=kind, resolution=res, selection_class=sel,
                                                 chain=chain, consistency=cons, source_repackaged=rep, source_has_direct=direct),
                             (status, list(reasons)))

    def test_the_evidence_chain_keeps_both_endpoints_and_every_step(self):
        chain = lineage.evidence_chain(self.conn, R["ok"][1])
        self.assertEqual(len(chain), 1)
        step = chain[0]
        self.assertEqual(step["relationship"], "SOURCE_LINKED_MANUFACTURING_EVIDENCE")
        self.assertIn('code="33333-0001"', step["citing"]["element"])
        self.assertIn('code="C64637"', step["citing"]["element"])
        self.assertEqual(step["source"]["set_id"], sid(51))
        self.assertEqual(step["source_direct_manufacture"]["duns"], X)
        self.assertIn('code="C43360"', step["source_direct_manufacture"]["element"])
        self.assertEqual(step["registration"]["file"], "drls_reg.zip")
        excluded = lineage.evidence_chain(self.conn, R["none"][1])
        self.assertEqual([(s["relationship"], s["status"]) for s in excluded], [("SOURCE_NDC_REFERENCE", "EXCLUDED")])


@unittest.skipUnless(available(), f"PostgreSQL test database {TEST_DB!r} not reachable")
class LineageV2Db(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        assert TEST_DB != "fineprint", "refusing to run destructive tests on the main database"
        cls.tmp = tempfile.TemporaryDirectory()
        root = Path(cls.tmp.name)
        build_fixture(root)
        cls.manifest, cls.cache = write_history(root)
        cls.conn = db.connect(TEST_DB, autocommit=True)
        cls.national = db.fingerprint(cls.conn)
        lineage.build(cls.conn, log=lambda m: None)
        cls.v1 = lineage.fingerprint(cls.conn)
        cls.first = lineage.validate_v2(cls.conn, cls.manifest, cls.cache, log=lambda m: None)

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()
        cls.tmp.cleanup()

    def check(self, key):
        return self.conn.execute(
            """SELECT c.classification, v.status, v.reasons, c.continuing_sites, c.applicable_version
               FROM lineage.version_check c JOIN lineage.resolution_v2 v USING (reference_pk) WHERE c.citing_ndc = %s""",
            (v2_citing(key)[1],)).fetchone()

    def tiers(self, code):
        return (self.conn.execute("SELECT coverage_tier FROM lineage.v_product_coverage WHERE ndc_raw = %s", (code,)).fetchone()[0],
                self.conn.execute("SELECT coverage_tier FROM lineage.v_product_coverage_v2 WHERE ndc_raw = %s", (code,)).fetchone()[0])

    def test_every_current_conflict_is_checked_and_gets_its_preregistered_class(self):
        expect = {
            "drift": ("VERSION_DRIFT_RESOLVED", "ELIGIBLE", [], [X], 1),
            "sitechg": ("VERSION_DRIFT_RESOLVED", "EXCLUDED", ["version:sites_changed_since_citing"], [], 1),
            "conflict": ("CONFIRMED_CONFLICT", "EXCLUDED", ["version:CONFIRMED_CONFLICT"], None, 1),
            "notation": ("NOTATION_ONLY", "ELIGIBLE", [], [X], 1),
            "several": ("MULTIPLE_VALID_PRESENTATIONS", "ELIGIBLE", [], [X], 1),
            "nohist": ("MISSING_COMPARISON_EVIDENCE", "EXCLUDED", ["version:MISSING_COMPARISON_EVIDENCE"], None, None),
            "earlier": ("UNRESOLVED_AMBIGUITY", "EXCLUDED", ["version:UNRESOLVED_AMBIGUITY"], None, 2),
            "unstated": ("MISSING_COMPARISON_EVIDENCE", "EXCLUDED", ["version:MISSING_COMPARISON_EVIDENCE"], None, 1),
            "postdates": ("UNRESOLVED_AMBIGUITY", "EXCLUDED", ["version:UNRESOLVED_AMBIGUITY"], None, None),
            "nosite": ("VERSION_DRIFT_RESOLVED", "EXCLUDED", ["version:no_site_named_at_applicable_version"], [], 1),
        }
        for key, (cls, status, reasons, sites, app) in expect.items():
            got = self.check(key)
            self.assertIsNotNone(got, key)
            self.assertEqual((got[0], got[1], list(got[2]), got[3], got[4]), (cls, status, reasons, sites, app), key)
        self.assertEqual(self.conn.execute("SELECT count(*) FROM lineage.version_check").fetchone()[0], len(expect))

    def test_a_reference_without_a_current_conflict_keeps_its_v1_result(self):
        self.assertIsNone(self.check("agree"))
        rows = self.conn.execute(
            """SELECT count(*) FROM lineage.source_resolution x JOIN lineage.resolution_v2 v USING (reference_pk)
               WHERE v.basis = 'v1' AND (v.status <> x.status OR v.reasons <> x.reasons)""").fetchone()[0]
        self.assertEqual(rows, 0)
        self.assertEqual(self.tiers(v2_citing("agree")[1]), ("SOURCE_LINKED", "SOURCE_LINKED"))
        self.assertEqual(self.tiers(R["ok"][1]), ("SOURCE_LINKED", "SOURCE_LINKED"))

    def test_v2_only_removes_links_and_keeps_only_continuing_sites(self):
        self.assertEqual(self.tiers(v2_citing("drift")[1]), ("SOURCE_LINKED", "SOURCE_LINKED"))
        for key in ("conflict", "sitechg", "earlier", "nohist", "unstated", "postdates", "nosite"):
            self.assertEqual(self.tiers(v2_citing(key)[1]), ("SOURCE_LINKED", "NO_MANUFACTURE_EVIDENCE"), key)
        added = self.conn.execute(
            """SELECT count(*) FROM lineage.source_linked_evidence_v2 e2 WHERE NOT EXISTS (
                   SELECT 1 FROM lineage.source_linked_evidence e
                   WHERE e.reference_pk = e2.reference_pk AND e.source_assertion_pk = e2.source_assertion_pk)""").fetchone()[0]
        self.assertEqual(added, 0)

    def test_dates_versions_and_the_fetch_path_check_are_recorded(self):
        row = self.conn.execute(
            """SELECT citing_published_at::text, citing_date_basis, source_version_now, applicable_published_at::text,
                      sites_at_applicable, canonical_xml_matches_release, versions_matching
               FROM lineage.version_check WHERE citing_ndc = %s""", (v2_citing("earlier")[1],)).fetchone()
        self.assertEqual(row, (D, "dailymed_history", 3, "2020-01-01", [X], True, [1]))
        docs = self.conn.execute("SELECT count(*), count(*) FILTER (WHERE status = 'ok') "
                                 "FROM lineage.source_version_document").fetchone()
        self.assertEqual(docs, (sum(len(v[2]) for k, v in V2.items() if k != "nohist"),) * 2)

    def test_v1_and_national_tables_are_untouched_and_v2_is_reproducible(self):
        self.assertEqual(lineage.fingerprint(self.conn), self.v1)
        self.assertEqual(db.fingerprint(self.conn), self.national)
        again = lineage.validate_v2(self.conn, self.manifest, self.cache, log=lambda m: None)
        self.assertEqual(again["fingerprint"], self.first["fingerprint"])

    def test_a_cached_archive_that_differs_from_the_manifest_is_refused(self):
        tampered = Path(self.tmp.name) / "tampered"
        shutil.copytree(self.cache, tampered)
        victim = next((tampered / "spl").iterdir())
        victim.write_bytes(victim.read_bytes() + b"\0")
        with self.assertRaises(ValueError):
            lineage.validate_v2(self.conn, self.manifest, tampered, log=lambda m: None)
        self.assertEqual(lineage.fingerprint_v2(self.conn), self.first["fingerprint"])

    def test_the_evidence_chain_reports_the_version_check(self):
        (step,) = lineage.evidence_chain(self.conn, v2_citing("drift")[1])
        self.assertEqual((step["v2"]["status"], step["v2"]["evidence_sites"], step["v2"]["this_site_kept_by_v2"]),
                         ("ELIGIBLE", [X], True))
        self.assertEqual(step["v2"]["version_check"]["classification"], "VERSION_DRIFT_RESOLVED")
        self.assertEqual(step["v2"]["version_check"]["applicable_version"], 1)


if __name__ == "__main__":
    unittest.main()

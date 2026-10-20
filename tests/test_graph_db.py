"""DST-02/03: version selection, dated identity, edge confidence and CLI answers on a synthetic release.

Runs against FINEPRINT_TEST_DB (default 'fineprint_test'); the national schema there is rebuilt.
"""

import os
import tempfile
import unittest
from pathlib import Path

from tests import release_builder as rb
from tests import spl_factory as sf

from fineprint import graph  # pure rules: no database driver needed

try:
    from fineprint import cli, db, identity, ingest
except ImportError:
    db = None

TEST_DB = os.environ.get("FINEPRINT_TEST_DB", "fineprint_test")
L, S1, S2, S3, S4, S5, S6, S7 = ("111111111", "200000001", "200000002", "200000003", "200000004", "200000005",
                                 "200000006", "200000007")
MFG = ("C43360", "MANUFACTURE")
PACK = ("C84731", "PACK")
SETS = {k: f"00000000-0000-4000-8000-00000000000{i}" for i, k in enumerate("ABCDEFGH", 1)}


def available():
    if db is None:
        return False
    try:
        db.connect(TEST_DB, connect_timeout=3).close()
        return True
    except Exception:
        return False


def documents():
    x = sf.spl_xml
    return [
        # set A: two versions; metadata names v2, so v1's McPherson-like site must vanish from the current graph
        ("A", 1, x(SETS["A"], 1, products=[("11111-0001", "Naloxone", [])],
                   establishments=[(S2, "Site Two", [(*MFG, ["11111-0001"])])])),
        ("A", 2, x(SETS["A"], 2, products=[("11111-0001", "Naloxone", ["11111-0001-01"])],
                   establishments=[(S1, "Site One", [(*MFG, ["11111-0001"])])])),
        # set B: a DIFFERENT product with the same name, made at S2; labeler L also PACKs it
        ("B", 3, x(SETS["B"], 3, products=[("11111-0002", "Naloxone", ["11111-0002-01"])],
                   establishments=[(S2, "Site Two", [(*MFG, ["11111-0002"])]), (L, "Labeler Co", [(*PACK, ["11111-0002"])])])),
        # set C: not in metadata; partial (no FEI) and missing identities
        ("C", 1, x(SETS["C"], 1, products=[("11111-0003", "Drug C", [])],
                   establishments=[(S3, "Site Three", [(*MFG, ["11111-0003"])]), (S5, "Ghost", [(*MFG, ["11111-0003"])])])),
        # set D: metadata names v5, release only has v2 -> ambiguous selection
        ("D", 2, x(SETS["D"], 2, products=[("11111-0004", "Drug D", [])],
                   establishments=[(S1, "Site One", [(*MFG, ["11111-0004"])])])),
        # set E: no establishment block at all
        ("E", 1, x(SETS["E"], 1, products=[("11111-0005", "Drug E", [])], with_block=False)),
        # set F: stale, FEI-changed and excluded identities
        ("F", 1, x(SETS["F"], 1, products=[("11111-0006", "Drug F", [])],
                   establishments=[(S4, "Old Site", [(*MFG, ["11111-0006"])]), (S6, "Moved", [(*MFG, ["11111-0006"])]),
                                   (S7, "Excluded", [(*MFG, ["11111-0006"])])])),
        # set G: MANUFACTURE not scoped to any product
        ("G", 1, x(SETS["G"], 1, products=[("11111-0007", "Drug G", [])],
                   establishments=[(S1, "Site One", [(*MFG, [])])])),
        # set H: same version, different bytes -> unresolved
        ("H", 1, x(SETS["H"], 1, products=[("11111-0008", "Drug H", [])], note="a",
                   establishments=[(S1, "Site One", [(*MFG, ["11111-0008"])])])),
        ("H", 1, x(SETS["H"], 1, products=[("11111-0008", "Drug H", [])], note="b",
                   establishments=[(S1, "Site One", [(*MFG, ["11111-0008"])])])),
    ]


def build_fixture(root: Path):
    members = [(f"prescription/20260101_{SETS[k]}_v{v}_{i}.zip", sf.nested(xml))
               for i, (k, v, xml) in enumerate(documents())]
    manifest = rb.write_manifest(root, {"synthetic_part.zip": members})
    meta_path = root / "dm_spl_zip_files_meta_data.zip"
    meta_lines = ["SETID|ZIP_FILE_NAME|UPLOAD_DATE|SPL_VERSION|TITLE",
                  f"{SETS['A']}|{members[1][0].split('/')[1]}|01/02/2026|2|A",
                  f"{SETS['B']}|{members[2][0].split('/')[1]}|01/03/2026|3|B",
                  f"{SETS['D']}|elsewhere.zip|01/04/2026|5|D",
                  f"{SETS['E']}|{members[5][0].split('/')[1]}|01/05/2026|1|E",
                  f"{SETS['F']}|{members[6][0].split('/')[1]}|01/06/2026|1|F",
                  f"{SETS['G']}|{members[7][0].split('/')[1]}|01/07/2026|1|G",
                  f"{SETS['H']}|nope.zip|01/08/2026|1|H"]
    meta_rec = sf.write_zip_text(meta_path, "dm_spl_zip_files_meta_data.txt", "\n".join(meta_lines) + "\n")
    cur = sf.decrs_text([
        {"FEI_NUMBER": "3000000001", "DUNS_NUMBER": S1, "FIRM_NAME": "Site One Inc", "ADDRESS": "1 Plant Rd",
         "EXPIRATION_DATE": "12/31/2026"},
        {"FEI_NUMBER": "3000000002", "DUNS_NUMBER": S2, "FIRM_NAME": "Site Two Inc", "ADDRESS": "2 Plant Rd",
         "EXPIRATION_DATE": "12/31/2026"},
        {"FEI_NUMBER": "", "DUNS_NUMBER": S3, "FIRM_NAME": "Site Three", "ADDRESS": "3 Plant Rd",
         "EXPIRATION_DATE": "12/31/2026"},
        {"FEI_NUMBER": "3000000006", "DUNS_NUMBER": S6, "FIRM_NAME": "Moved Inc", "ADDRESS": "6 New Rd",
         "EXPIRATION_DATE": "12/31/2026"},
        {"FEI_NUMBER": "3000000077", "DUNS_NUMBER": L, "FIRM_NAME": "Labeler Co", "ADDRESS": "HQ",
         "EXPIRATION_DATE": "12/31/2026", "OPERATIONS": "PACK"}])
    old = sf.decrs_text([
        {"FEI_NUMBER": "3000000004", "DUNS_NUMBER": S4, "FIRM_NAME": "Old Site", "ADDRESS": "4 Old Rd",
         "EXPIRATION_DATE": "12/31/2025"},
        {"FEI_NUMBER": "3000000099", "DUNS_NUMBER": S6, "FIRM_NAME": "Moved Inc", "ADDRESS": "6 Old Rd",
         "EXPIRATION_DATE": "12/31/2025"}])
    exc = sf.decrs_text([{"FEI_NUMBER": "", "DUNS_NUMBER": S7, "FIRM_NAME": "Excluded", "ADDRESS": "7 Rd",
                          "EXPIRATION_DATE": "", "EXCLUSION_FLAG": "E"}])
    regs = [("fda_decrs_registration", root / "cur" / "drls_reg.zip", "drls_reg.txt", cur, (2026, 10, 19, 3, 0, 0)),
            ("fda_decrs_excluded", root / "cur" / "drls_excluded.zip", "drls_excluded.txt", exc, (2026, 10, 19, 3, 0, 0)),
            ("fda_decrs_registration_archived", root / "old" / "drls_reg.zip", "drls_reg.txt", old,
             (2025, 12, 5, 3, 0, 0))]
    with db.connect(TEST_DB, autocommit=True) as c:
        db.reset_national(c)
        db.migrate(c)
        inputs = ingest.release_inputs(manifest)
        run_id = ingest.start_run(c, {"test": "graph"})
        sid, _ = ingest.register_source(c, kind="dailymed_zip_metadata",
                                        advertised={"name": meta_path.name, "advertised_md5": meta_rec["md5"]},
                                        record=meta_rec, path=meta_path, release_label="2026-10-16", verify=False)
        ingest.load_zip_metadata(c, sid, meta_path)
        p = inputs["parts"][0]
        psid, _ = ingest.register_source(c, kind="dailymed_human_rx_full_part", advertised=p["advertised"],
                                         record=p["record"], path=p["path"], release_label="2026-10-16", verify=False)
        ingest.ingest_part(c, source_file_id=psid, path=p["path"], run_id=run_id, log=lambda m: None)
        ingest.resolve_published_dates(c)
        ingest.refresh_operation_types(c, run_id)
        ingest.finish_run(c, run_id, "completed", {})
        for kind, path, member, text, when in regs:
            rec = sf.write_zip_text(path, member, text, date_time=when)
            rows, info = identity.parse_decrs(path)
            fsid, _ = identity.register_file(c, kind=kind, path=path, record=rec, release_label=info["generated_at"][:10],
                                             generated_at=info["generated_at"])
            identity.load_rows(c, fsid, rows)
        graph.build(c, log=lambda m: None)


@unittest.skipUnless(available(), f"PostgreSQL test database {TEST_DB!r} not reachable")
class GraphDb(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        assert TEST_DB != "fineprint"
        cls.tmp = tempfile.TemporaryDirectory()
        build_fixture(Path(cls.tmp.name))
        cls.conn = db.connect(TEST_DB)

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()
        cls.tmp.cleanup()

    def q(self, sql, *a):
        return self.conn.execute(sql, a).fetchall()

    def cli(self, *argv):
        return cli.run(["--db", TEST_DB, *argv], conn=self.conn)

    def test_version_selection(self):
        got = dict(self.q("SELECT set_id, selection_status || ':' || coalesce(selected_version::text, '-') "
                          "FROM national.set_version_selection"))
        self.assertEqual(got[SETS["A"]], "MULTI_VERSION_METADATA_SELECTED:2")
        self.assertEqual(got[SETS["B"]], "SINGLE_VERSION_METADATA_CONFIRMED:3")
        self.assertEqual(got[SETS["C"]], "SINGLE_VERSION_NOT_IN_METADATA:1")
        self.assertEqual(got[SETS["D"]], "SINGLE_VERSION_METADATA_LISTS_OTHER:2")
        self.assertEqual(got[SETS["H"]], "UNRESOLVED_SAME_VERSION_CONFLICT:1")
        # every raw version is still stored
        self.assertEqual(self.q("SELECT count(*) FROM national.spl_document WHERE set_id = %s", SETS["A"])[0][0], 2)
        # published date only from official metadata, never from the filename prefix
        pub = dict(self.q("SELECT set_id, published_date::text FROM national.set_version_selection"))
        self.assertEqual(pub[SETS["A"]], "2026-01-02")
        self.assertIsNone(pub[SETS["C"]])

    def test_identity_statuses(self):
        got = dict(self.q("SELECT duns, status FROM national.duns_identity"))
        self.assertEqual(got[S1], "CURRENT_REGISTERED")
        self.assertEqual(got[S3], "CURRENT_REGISTERED_NO_FEI")
        self.assertEqual(got[S4], "STALE_REGISTERED")
        self.assertEqual(got[S5], "NOT_FOUND")
        self.assertEqual(got[S7], "CURRENT_EXCLUDED")
        moved = self.q("SELECT fei, fei_changed FROM national.duns_identity WHERE duns = %s", S6)[0]
        self.assertEqual(moved, ("3000000006", True))
        # contact columns never reach the database
        cols = {r[0] for r in self.q("SELECT column_name FROM information_schema.columns "
                                     "WHERE table_schema='national' AND table_name='registration_record'")}
        self.assertFalse(cols & {"establishment_contact_name", "establishment_contact_email", "agent_details"})
        self.assertEqual(self.q("SELECT count(*) FROM national.registration_record WHERE "
                                "concat_ws(' ', firm_name, address, operations_raw, registrant_name) ILIKE %s",
                                "%example.invalid%")[0][0], 0)
        self.assertEqual(self.q("SELECT count(*) FROM national.registration_record WHERE "
                                "concat_ws(' ', firm_name, registrant_name) ILIKE %s", "%Test Person%")[0][0], 0)

    def test_edge_confidence_matches_pure_rule(self):
        rows = self.q("""SELECT e.duns, e.identity_status, coalesce(i.evidence_expiration < i.evidence_as_of, false),
                                coalesce(i.fei_changed, false), e.product_scope, e.selection_class, e.confidence,
                                e.confidence_reasons
                         FROM national.operation_edge e LEFT JOIN national.duns_identity i USING (duns)""")
        self.assertGreater(len(rows), 8)
        for duns, status, expired, changed, scope, sel, conf, reasons in rows:
            self.assertEqual(graph.edge_confidence(duns=duns, identity_status=status, expired=expired,
                                                   fei_changed=changed, scope=scope, selection_class=sel),
                             (conf, list(reasons)))

    def sites(self, ndc):
        res = self.cli("product", ndc)
        (p,) = res["products"]
        return {c: sorted(e["duns"] for e in p["manufacturing_sites"][c]) for c in ("DIRECT", "TENTATIVE", "UNKNOWN")}, p

    def test_duplicate_versions_only_canonical_edges(self):
        sites, p = self.sites("11111-0001")
        self.assertEqual(sites, {"DIRECT": [S1], "TENTATIVE": [], "UNKNOWN": []})  # v1's S2 never leaks in
        self.assertEqual(p["version"], 2)
        self.assertEqual(p["versions_in_release"], [1, 2])

    def test_misleading_same_name_products_stay_separate(self):
        self.assertEqual(self.sites("11111-0001")[0]["DIRECT"], [S1])
        self.assertEqual(self.sites("11111-0002")[0]["DIRECT"], [S2])
        found = self.cli("search", "naloxone")["products"]
        self.assertEqual(sorted(r["ndc_product_5_4"] for r in found), ["11111-0001", "11111-0002"])
        # package lookup goes through the explicit segment relationship
        self.assertEqual([p["ndc_product_5_4"] for p in self.cli("product", "11111-0002-01")["products"]],
                         ["11111-0002"])

    def test_partial_and_missing_identities_are_not_direct(self):
        self.assertEqual(self.sites("11111-0003")[0], {"DIRECT": [], "TENTATIVE": [S3], "UNKNOWN": [S5]})
        self.assertEqual(self.sites("11111-0004")[0]["TENTATIVE"], [S1])  # ambiguous version selection
        self.assertEqual(self.sites("11111-0006")[0], {"DIRECT": [], "TENTATIVE": [S4, S6, S7], "UNKNOWN": []})

    def test_missing_establishment_block_and_unscoped(self):
        _, p = self.sites("11111-0005")
        self.assertEqual(p["evidence_status"], "NO_ESTABLISHMENT_BLOCK")
        self.assertIn("no establishments", p["why_no_site"])
        _, g = self.sites("11111-0007")
        self.assertEqual(g["evidence_status"], "ONLY_UNSCOPED_OPERATIONS_IN_DOCUMENT")
        self.assertEqual(g["document_level_unscoped_operations"], 1)
        self.assertEqual(self.cli("product", "11111-0008")["products"], [])  # unresolved set: not in current graph

    def test_facility_queries(self):
        f = self.cli("facility", S2)
        self.assertEqual([e["ndc_product_5_4"] for e in f["products_by_confidence"]["DIRECT"]], ["11111-0002"])
        lab = self.cli("facility", L)
        self.assertEqual(sum(len(v) for v in lab["products_by_confidence"].values()), 0)  # PACK is not MANUFACTURE
        self.assertGreater(lab["documents_where_this_duns_is_the_labeler"], 0)
        self.assertEqual([o["operation"] for o in lab["other_operations_summary"]], ["PACK"])
        by_fei = self.cli("facility", "FEI:3000000001")
        self.assertEqual(sorted(e["ndc_product_5_4"] for e in by_fei["products_by_confidence"]["DIRECT"]),
                         ["11111-0001"])
        cmp = self.cli("compare", S1, S2)
        self.assertEqual(cmp["counts"], {"only_a": 2, "only_b": 1, "both": 0})

    def test_evidence_resolves_to_raw_xml(self):
        (eid,) = self.q("SELECT assertion_pk FROM national.operation_edge WHERE product_ndc_raw='11111-0002' "
                        "AND is_manufacture")[0]
        ev = self.cli("evidence", str(eid), "--raw")["evidence"]
        self.assertEqual((ev["duns"], ev["operation_code"], ev["confidence"]), (S2, "C43360", "DIRECT"))
        self.assertIn('code="C43360"', ev["raw_xml"])
        self.assertIn('code="11111-0002"', ev["raw_xml"])

    def test_unhyphenated_ndc_is_refused(self):
        with self.assertRaises(cli.UserError):
            self.cli("product", "11111000201")

    def test_rebuild_is_idempotent_and_base_untouched(self):
        base = db.fingerprint(self.conn)
        before = graph.fingerprint(self.conn)
        self.conn.commit()
        with db.connect(TEST_DB, autocommit=True) as c:
            graph.build(c, log=lambda m: None)
        self.assertEqual(graph.fingerprint(self.conn), before)
        self.assertEqual(db.fingerprint(self.conn), base)


class PureRules(unittest.TestCase):
    def test_select_version_prefers_metadata_then_highest(self):
        docs = [(1, 1, "a"), (2, 2, "b"), (3, 3, "c")]
        self.assertEqual(graph.select_version(docs, 2)["document_pk"], 2)
        self.assertEqual(graph.select_version(docs, None)["status"], "MULTI_VERSION_HIGHEST_NO_METADATA")
        self.assertEqual(graph.select_version(docs, 9)["class"], "ambiguous")
        self.assertEqual(graph.select_version([(1, 1, "a"), (2, 1, "b")], 1)["class"], "unresolved")

    def test_edge_confidence_rules(self):
        base = dict(duns="1", identity_status="CURRENT_REGISTERED", expired=False, fei_changed=False,
                    scope="product", selection_class="confirmed")
        self.assertEqual(graph.edge_confidence(**base), ("DIRECT", []))
        self.assertEqual(graph.edge_confidence(**{**base, "selection_class": "unconfirmed"})[0], "DIRECT")
        self.assertEqual(graph.edge_confidence(**{**base, "identity_status": "NOT_FOUND"})[0], "UNKNOWN")
        self.assertEqual(graph.edge_confidence(**{**base, "scope": "no_product_scope"})[0], "UNKNOWN")
        self.assertEqual(graph.edge_confidence(**{**base, "expired": True}),
                         ("TENTATIVE", ["identity:registration_expired"]))


if __name__ == "__main__":
    unittest.main()

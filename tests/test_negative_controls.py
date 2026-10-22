"""Product-level negative controls (research workstream B2): what must NOT become a manufacturing site.

Pure-rule tests run everywhere. The database tests build a small synthetic release in FINEPRINT_TEST_DB and check the
graph tables and views for every control type in docs/research/AUDIT_CONTROLS_V2.md:

  PACK / LABEL / ANALYSIS without MANUFACTURE, API MANUFACTURE only, API site versus finished-dose site,
  MANUFACTURE with no product scope in a single-product label, MANUFACTURE by an unresolved or stale DUNS.
"""

import os
import tempfile
import unittest
from pathlib import Path

from tests import release_builder as rb
from tests import spl_factory as sf

from fineprint import graph, spl

try:
    from fineprint import db, identity, ingest
except ImportError:
    db = None

TEST_DB = os.environ.get("FINEPRINT_TEST_DB", "fineprint_test")
LAB, X, Y, GHOST, OLD = "111111111", "300000001", "300000002", "300000009", "300000004"
MFG, API, PACK, LABEL, ANALYSIS = (("C43360", "MANUFACTURE"), ("C82401", "API MANUFACTURE"), ("C84731", "PACK"),
                                  ("C84732", "LABEL"), ("C25391", "ANALYSIS"))
SETS = {k: f"00000000-0000-4000-8000-0000000000{i:02d}" for i, k in enumerate("PLAQBUNS", 11)}
NDC = {"P": "22222-0001", "L": "22222-0002", "A": "22222-0003", "Q": "22222-0004", "B": "22222-0005",
       "U": "22222-0006", "N": "22222-0007", "S": "22222-0008"}


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
    one = lambda k, ests: x(SETS[k], 1, products=[(NDC[k], f"Drug {k}", [NDC[k] + "-01"])], establishments=ests)  # noqa: E731
    return [
        ("P", one("P", [(X, "Packer", [(*PACK, [NDC["P"]])])])),                       # PACK without MANUFACTURE
        ("L", one("L", [(X, "Labeler site", [(*LABEL, [NDC["L"]])])])),                # LABEL without MANUFACTURE
        ("A", one("A", [(X, "Lab", [(*ANALYSIS, [NDC["A"]])])])),                      # ANALYSIS without MANUFACTURE
        ("Q", one("Q", [(X, "API plant", [(*API, [NDC["Q"]])])])),                     # API MANUFACTURE only
        ("B", one("B", [(X, "API plant", [(*API, [NDC["B"]])]), (Y, "Dose plant", [(*MFG, [NDC["B"]])])])),  # API vs FDF
        ("U", one("U", [(X, "Site", [(*MFG, [])])])),                                  # unscoped MANUFACTURE, 1 product
        ("N", one("N", [(GHOST, "Ghost", [(*MFG, [NDC["N"]])])])),                     # unresolved DUNS
        ("S", one("S", [(OLD, "Old site", [(*MFG, [NDC["S"]])])])),                    # stale registration
    ]


def build_fixture(root: Path):
    members = [(f"prescription/20260101_{SETS[k]}.zip", sf.nested(xml)) for k, xml in documents()]
    manifest = rb.write_manifest(root, {"controls_part.zip": members})
    cur = sf.decrs_text([
        {"FEI_NUMBER": "3000000001", "DUNS_NUMBER": X, "FIRM_NAME": "X Inc", "ADDRESS": "1 X Rd", "EXPIRATION_DATE": "12/31/2026"},
        {"FEI_NUMBER": "3000000002", "DUNS_NUMBER": Y, "FIRM_NAME": "Y Inc", "ADDRESS": "2 Y Rd", "EXPIRATION_DATE": "12/31/2026"},
        {"FEI_NUMBER": "3000000077", "DUNS_NUMBER": LAB, "FIRM_NAME": "Labeler Co", "ADDRESS": "HQ", "EXPIRATION_DATE": "12/31/2026"}])
    old = sf.decrs_text([{"FEI_NUMBER": "3000000004", "DUNS_NUMBER": OLD, "FIRM_NAME": "Old Site", "ADDRESS": "4 Old Rd",
                          "EXPIRATION_DATE": "12/31/2025"}])
    regs = [("fda_decrs_registration", root / "cur" / "drls_reg.zip", "drls_reg.txt", cur, (2026, 10, 19, 3, 0, 0)),
            ("fda_decrs_excluded", root / "cur" / "drls_excluded.zip", "drls_excluded.txt", sf.decrs_text([]), (2026, 10, 19, 3, 0, 0)),
            ("fda_decrs_registration_archived", root / "old" / "drls_reg.zip", "drls_reg.txt", old, (2025, 12, 5, 3, 0, 0))]
    with db.connect(TEST_DB, autocommit=True) as c:
        db.reset_national(c)
        db.migrate(c)
        inputs = ingest.release_inputs(manifest)
        run_id = ingest.start_run(c, {"test": "negative_controls"})
        p = inputs["parts"][0]
        psid, _ = ingest.register_source(c, kind="dailymed_human_rx_full_part", advertised=p["advertised"],
                                         record=p["record"], path=p["path"], release_label="2026-10-16", verify=False)
        ingest.ingest_part(c, source_file_id=psid, path=p["path"], run_id=run_id, log=lambda m: None)
        ingest.refresh_operation_types(c, run_id)
        ingest.finish_run(c, run_id, "completed", {})
        for kind, path, member, text, when in regs:
            rec = sf.write_zip_text(path, member, text, date_time=when)
            rows, info = identity.parse_decrs(path)
            fsid, _ = identity.register_file(c, kind=kind, path=path, record=rec, release_label=info["generated_at"][:10],
                                             generated_at=info["generated_at"])
            identity.load_rows(c, fsid, rows)
        graph.build(c, log=lambda m: None)


class PureRules(unittest.TestCase):
    def test_only_c43360_is_manufacture(self):
        self.assertEqual(spl.MANUFACTURE_CODE, "C43360")
        for code in ("C82401", "C84731", "C84732", "C25391", "C73606", "C73607", "C101510"):
            self.assertNotEqual(code, spl.MANUFACTURE_CODE)

    def test_unscoped_manufacture_is_unknown_even_with_perfect_identity(self):
        self.assertEqual(graph.edge_confidence(duns=X, identity_status="CURRENT_REGISTERED", expired=False,
                                               fei_changed=False, scope="no_product_scope", selection_class="confirmed"),
                         ("UNKNOWN", ["scope:no_product_scope"]))

    def test_unresolved_and_stale_identity_never_direct(self):
        self.assertEqual(graph.edge_confidence(duns=GHOST, identity_status="NOT_FOUND", expired=False, fei_changed=False,
                                               scope="product", selection_class="confirmed"),
                         ("UNKNOWN", ["identity:NOT_FOUND"]))
        self.assertEqual(graph.edge_confidence(duns=OLD, identity_status="STALE_REGISTERED", expired=False,
                                               fei_changed=False, scope="product", selection_class="confirmed"),
                         ("TENTATIVE", ["identity:STALE_REGISTERED"]))

    def test_parser_keeps_api_manufacture_distinct(self):
        import io
        doc = spl.parse_spl(io.BytesIO(documents()[4][1]))
        edges = spl.operation_edges(doc)
        self.assertEqual(sorted((e["duns"], e["operation_code"]) for e in edges), [(X, "C82401"), (Y, "C43360")])


@unittest.skipUnless(available(), f"PostgreSQL test database {TEST_DB!r} not reachable")
class NegativeControlsDb(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        assert TEST_DB != "fineprint", "refusing to run destructive tests on the main database"
        cls.tmp = tempfile.TemporaryDirectory()
        build_fixture(Path(cls.tmp.name))
        cls.conn = db.connect(TEST_DB)

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()
        cls.tmp.cleanup()

    def status(self, key):
        row = self.conn.execute("SELECT manufacturing_status, evidence_status, manufacture_duns FROM "
                                "national.v_product_manufacturing_status WHERE ndc_product_5_4 = %s", (NDC[key],)).fetchone()
        self.assertIsNotNone(row, key)
        return row

    def edges(self, key):
        return self.conn.execute(
            """SELECT e.operation_code, e.is_manufacture, e.duns, e.confidence, e.confidence_reasons, e.product_scope
               FROM national.operation_edge e WHERE e.product_ndc_5_4 = %s OR (e.product_scope = 'no_product_scope'
               AND e.set_id = %s) ORDER BY 1, 3""", (NDC[key], SETS[key])).fetchall()

    def test_pack_label_analysis_are_not_manufacture(self):
        for key, code in (("P", "C84731"), ("L", "C84732"), ("A", "C25391")):
            status, evidence, n = self.status(key)
            self.assertEqual((status, evidence, n), ("NO_MANUFACTURE_EVIDENCE", "OTHER_OPERATIONS_ONLY", 0), key)
            edges = self.edges(key)
            self.assertEqual([(e[0], e[1], e[3]) for e in edges], [(code, False, "DIRECT")], key)

    def test_api_manufacture_only_is_not_a_manufacturing_site(self):
        status, evidence, n = self.status("Q")
        self.assertEqual((status, evidence, n), ("NO_MANUFACTURE_EVIDENCE", "OTHER_OPERATIONS_ONLY", 0))
        self.assertEqual([(e[0], e[1]) for e in self.edges("Q")], [("C82401", False)])
        name = self.conn.execute("SELECT operation_name FROM national.operation_edge WHERE product_ndc_5_4 = %s",
                                 (NDC["Q"],)).fetchone()[0]
        self.assertEqual(name, "API MANUFACTURE")

    def test_api_site_is_not_counted_beside_the_finished_dose_site(self):
        status, evidence, n = self.status("B")
        self.assertEqual((status, evidence, n), ("DIRECT", "EXPLICIT_MANUFACTURE", 1))
        mfg = [e for e in self.edges("B") if e[1]]
        self.assertEqual([(e[2], e[3]) for e in mfg], [(Y, "DIRECT")])
        api = [e for e in self.edges("B") if e[0] == "C82401"]
        self.assertEqual([(e[2], e[1]) for e in api], [(X, False)])

    def test_unscoped_manufacture_in_single_product_label_is_not_attributed(self):
        status, evidence, n = self.status("U")
        self.assertEqual((status, evidence, n), ("NO_MANUFACTURE_EVIDENCE", "ONLY_UNSCOPED_OPERATIONS_IN_DOCUMENT", 0))
        edges = self.edges("U")
        self.assertEqual([(e[0], e[1], e[3], list(e[4]), e[5]) for e in edges],
                         [("C43360", True, "UNKNOWN", ["scope:no_product_scope"], "no_product_scope")])
        self.assertEqual(self.conn.execute("SELECT count(*) FROM national.operation_edge WHERE set_id = %s AND "
                                           "report_product_pk IS NOT NULL", (SETS["U"],)).fetchone()[0], 0)

    def test_unresolved_duns_is_unknown_site_never_direct(self):
        status, evidence, n = self.status("N")
        self.assertEqual((status, evidence, n), ("UNKNOWN_SITE", "EXPLICIT_MANUFACTURE", 1))
        self.assertEqual([(e[3], list(e[4])) for e in self.edges("N")], [("UNKNOWN", ["identity:NOT_FOUND"])])
        self.assertIsNone(self.conn.execute("SELECT fei FROM national.duns_identity WHERE duns = %s", (GHOST,)).fetchone()[0])

    def test_stale_registration_is_tentative_never_direct(self):
        status, evidence, n = self.status("S")
        self.assertEqual((status, evidence, n), ("TENTATIVE", "EXPLICIT_MANUFACTURE", 1))
        self.assertEqual([(e[3], list(e[4])) for e in self.edges("S")], [("TENTATIVE", ["identity:STALE_REGISTERED"])])

    def test_no_direct_edge_exists_for_any_control_product(self):
        n = self.conn.execute("""SELECT count(*) FROM national.operation_edge WHERE is_manufacture AND confidence = 'DIRECT'
                                 AND product_ndc_5_4 = ANY(%s)""",
                              ([NDC[k] for k in "PLAQUNS"],)).fetchone()[0]
        self.assertEqual(n, 0)


if __name__ == "__main__":
    unittest.main()

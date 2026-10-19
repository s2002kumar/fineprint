"""DST-01 ingestion against a real PostgreSQL test database (skipped when unavailable).

Uses database FINEPRINT_TEST_DB (default 'fineprint_test'); the national schema in it is
dropped and rebuilt by these tests. Never point this at the real 'fineprint' database.
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests import release_builder as rb

try:
    import psycopg  # noqa: F401
    from fineprint import db, ingest
except ImportError:  # stdlib-only environments still run the rest of the suite
    psycopg = None

TEST_DB = os.environ.get("FINEPRINT_TEST_DB", "fineprint_test")
REPO = Path(__file__).resolve().parents[1]
INGEST = REPO / "scripts" / "dst01_ingest.py"


def available():
    if psycopg is None:
        return False
    try:
        db.connect(TEST_DB, connect_timeout=3).close()
        return True
    except Exception:
        return False


@unittest.skipUnless(available(), f"PostgreSQL test database {TEST_DB!r} not reachable")
class IngestDb(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        assert TEST_DB != "fineprint", "refusing to run destructive tests on the main database"
        cls.tmp = tempfile.TemporaryDirectory()
        root = Path(cls.tmp.name)
        cls.manifest = rb.write_manifest(root / "a", {"part_a.zip": rb.standard_members()})
        dup = [(rb.member(rb.FIX["no_est"]), rb.nested(rb.xml("no_est")))]
        cls.manifest_ab = rb.write_manifest(root / "ab", {"part_a.zip": rb.standard_members(), "part_b.zip": dup})

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def run_cli(self, manifest, *extra):
        return subprocess.run([sys.executable, "-I", str(INGEST), "--manifest", str(manifest), "--db", TEST_DB,
                               "--no-verify", *extra], capture_output=True, text=True, cwd=REPO)

    def fresh(self):
        with db.connect(TEST_DB, autocommit=True) as c:
            db.reset_national(c)

    def fp(self):
        with db.connect(TEST_DB) as c:
            return db.fingerprint(c)

    def q(self, sql, *args):
        with db.connect(TEST_DB) as c:
            return c.execute(sql, args).fetchall()

    def test_1_load_semantics(self):
        self.fresh()
        r = self.run_cli(self.manifest, "--batch-size", "3")
        self.assertEqual(r.returncode, 0, r.stderr)
        status = dict(self.q("SELECT status, count(*) FROM national.archive_member GROUP BY 1"))
        self.assertEqual(status, {"loaded": 5, "failed": 3})
        stages = dict(self.q("SELECT stage, count(*) FROM national.dead_letter GROUP BY 1"))
        self.assertEqual(stages, {"nested_zip": 1, "xml": 1, "outer_member": 1})
        self.assertEqual(self.q("SELECT count(*) FROM national.v_version_conflicts")[0][0], 1)
        # Missing establishment evidence is its own state, never "not manufactured".
        ev = dict(self.q("SELECT set_id, evidence_status FROM national.v_product_establishment_evidence "
                         "WHERE kind = 'product' AND set_id IN (%s, %s)", rb.FIX["no_est"], rb.FIX["multi_est"]))
        self.assertEqual(ev[rb.FIX["no_est"]], "NO_ESTABLISHMENT_BLOCK")
        self.assertEqual(ev[rb.FIX["multi_est"]], "EXPLICIT_MANUFACTURE")
        # Operations only ever hang off establishment-level organizations, never the labeler.
        roles = self.q("SELECT DISTINCT o.role FROM national.operation_assertion a "
                       "JOIN national.organization_mention o ON o.org_pk = a.establishment_org_pk")
        self.assertEqual(roles, [("establishment",)])
        # Kit-part scoping is explicit.
        self.assertGreater(self.q("SELECT count(*) FROM national.operation_assertion WHERE product_scope='kit_part'")[0][0], 0)
        # API MANUFACTURE keeps its own code; it is not counted as MANUFACTURE.
        self.assertGreater(self.q("SELECT count(*) FROM national.operation_assertion WHERE operation_code='C82401'")[0][0], 0)
        canon = dict(self.q("SELECT operation_code, canonical_name FROM national.operation_type"))
        self.assertEqual(canon["C43360"], "MANUFACTURE")
        self.assertEqual(canon["C82401"], "API MANUFACTURE")
        # Product and package identifiers are normalized into different columns and shapes.
        bad_prod = self.q("SELECT count(*) FROM national.product WHERE ndc_product_5_4 !~ '^[0-9]{5}-[0-9]{4}$'")
        bad_pkg = self.q("SELECT count(*) FROM national.package WHERE ndc_package_5_4_2 !~ '^[0-9]{5}-[0-9]{4}-[0-9]{2}$'")
        self.assertEqual((bad_prod[0][0], bad_pkg[0][0]), (0, 0))
        self.assertEqual(self.q("SELECT count(*) FROM national.package WHERE segments_match_product IS FALSE")[0][0], 0)
        run = self.q("SELECT status FROM national.ingest_run ORDER BY run_id DESC LIMIT 1")[0][0]
        self.assertEqual(run, "completed_with_failures")

    def test_2_rerun_is_idempotent(self):
        self.fresh()
        self.assertEqual(self.run_cli(self.manifest).returncode, 0)
        before = self.fp()
        r = self.run_cli(self.manifest)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.fp(), before)
        self.assertEqual(self.q("SELECT count(*) FROM national.ingest_run")[0][0], 2)

    def test_3_crash_then_resume_matches_clean_run(self):
        self.fresh()
        self.assertEqual(self.run_cli(self.manifest, "--batch-size", "2").returncode, 0)
        clean = self.fp()
        self.fresh()
        crashed = self.run_cli(self.manifest, "--batch-size", "2", "--crash-after", "3")
        self.assertEqual(crashed.returncode, 137, crashed.stderr)
        partial = self.q("SELECT count(*) FROM national.archive_member")[0][0]
        self.assertEqual(partial, 2)  # only the first committed batch survived the hard exit
        resumed = self.run_cli(self.manifest, "--batch-size", "2")
        self.assertEqual(resumed.returncode, 0, resumed.stderr)
        self.assertEqual(self.fp(), clean)
        self.assertIn("interrupted", [r[0] for r in self.q("SELECT status FROM national.ingest_run")])

    def test_4_identical_document_in_two_parts_is_stored_once(self):
        self.fresh()
        self.assertEqual(self.run_cli(self.manifest_ab).returncode, 0)
        rows = self.q("""SELECT s.name, m.status FROM national.archive_member m
                         JOIN national.source_file s USING (source_file_id) WHERE s.name = 'part_b.zip'""")
        self.assertEqual(rows, [("part_b.zip", "duplicate")])
        self.assertEqual(self.q("SELECT count(*) FROM national.spl_document WHERE set_id = %s", rb.FIX["no_est"])[0][0], 1)

    def _ingest_in_process(self, read_member, **kw):
        with db.connect(TEST_DB, autocommit=True) as c:
            db.migrate(c)
            p = ingest.release_inputs(self.manifest)["parts"][0]
            run_id = ingest.start_run(c, {"test": "memory"})
            sid, _ = ingest.register_source(c, kind="dailymed_human_rx_full_part", advertised=p["advertised"],
                                            record=p["record"], path=p["path"], release_label="test", verify=False)
            real = ingest.safezip.read_member
            ingest.safezip.read_member = read_member(real)
            try:
                return ingest.ingest_part(c, source_file_id=sid, path=p["path"], run_id=run_id, batch_size=3,
                                          memory_backoff_s=0, log=lambda m: None, **kw)
            finally:
                ingest.safezip.read_member = real
                ingest.finish_run(c, run_id, "completed", {})

    def test_6_memory_error_retries_batch_and_never_dead_letters(self):
        self.fresh()
        calls = {"n": 0}

        def flaky_once(real):
            def f(*a, **k):
                calls["n"] += 1
                if calls["n"] == 2:
                    raise MemoryError("injected")
                return real(*a, **k)
            return f
        st = self._ingest_in_process(flaky_once)
        self.assertEqual(st["memory_error_batch_retries"], 1)
        self.assertEqual((st["loaded"], st["failed"], st["processed"]), (5, 3, 8))
        self.assertEqual(self.q("SELECT count(*) FROM national.dead_letter WHERE error_kind = 'MemoryError'")[0][0], 0)

    def test_7_persistent_memory_error_fails_run_without_partial_batch(self):
        self.fresh()

        def always(real):
            def f(*a, **k):
                raise MemoryError("injected")
            return f
        with self.assertRaises(MemoryError):
            self._ingest_in_process(always, memory_retries=1)
        self.assertEqual(self.q("SELECT count(*) FROM national.archive_member")[0][0], 0)
        self.assertEqual(self.q("SELECT count(*) FROM national.dead_letter")[0][0], 0)

    def test_5_migration_reapply_is_noop(self):
        with db.connect(TEST_DB, autocommit=True) as c:
            db.migrate(c)
            self.assertEqual(db.migrate(c), [])


if __name__ == "__main__":
    unittest.main()

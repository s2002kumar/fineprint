"""DST-06: incremental refresh from an update archive (additions, supersession, retraction, idempotence)."""

import hashlib
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from tests import spl_factory as sf
from tests.test_graph_db import MFG, S1, S2, SETS, TEST_DB, available, build_fixture

try:
    from fineprint import db, graph, ingest, refresh
except ImportError:
    db = None

SET_J = "00000000-0000-4000-8000-0000000000aa"
SET_OTC = "00000000-0000-4000-8000-0000000000bb"


def write_update(path: Path):
    x = sf.spl_xml
    members = {
        f"prescription/20261101_{SETS['A']}.zip": sf.nested(x(SETS["A"], 3, products=[("11111-0001", "Naloxone", [])],
                                                              establishments=[(S2, "Site Two", [(*MFG, ["11111-0001"])])])),
        f"prescription/20261101_{SET_J}.zip": sf.nested(x(SET_J, 1, products=[("11111-0009", "Drug J", [])],
                                                          establishments=[(S1, "Site One", [(*MFG, ["11111-0009"])])])),
        f"otc/20261101_{SET_OTC}.zip": sf.nested(x(SET_OTC, 1, products=[("22222-0001", "OTC", [])])),
    }
    deleted = [f"prescription/20260101_{SETS['B']}_v3_2.zip",      # set B withdrawn entirely
               f"prescription/20260101_{SETS['A']}_v2_1.zip",      # set A v2 superseded by v3
               "otc/20250101_ffffffff-0000-4000-8000-000000000000.zip"]
    with zipfile.ZipFile(path, "w", zipfile.ZIP_STORED) as z:
        for name, data in members.items():
            z.writestr(name, data)
        z.writestr("files_added.txt", "\n".join(members) + "\n")
        z.writestr("files_deleted.txt", "\n".join(deleted) + "\n")
    b = path.read_bytes()
    rec = {"url": "https://example.invalid/update.zip", "etag": None, "last_modified": None, "content_length": len(b),
           "bytes": len(b), "sha256": hashlib.sha256(b).hexdigest(), "md5": hashlib.md5(b).hexdigest(),
           "md5_matches_advertised": True, "first_started_at": None, "completed_at": "2026-11-01T00:00:00Z"}
    return rec, {"name": "dm_spl_daily_update_test.zip", "advertised_md5": rec["md5"]}


@unittest.skipUnless(db is not None and available(), f"PostgreSQL test database {TEST_DB!r} not reachable")
class RefreshDb(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        root = Path(cls.tmp.name)
        build_fixture(root)
        cls.update = root / "update.zip"
        cls.rec, cls.adv = write_update(cls.update)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def apply(self):
        with db.connect(TEST_DB, autocommit=True) as c:
            db.migrate(c)
            run_id = ingest.start_run(c, {"test": "refresh"})
            try:
                return refresh.apply_update(c, path=self.update, record=self.rec, advertised=self.adv,
                                            prefix="prescription/", run_id=run_id, verify=False, log=lambda m: None)
            finally:
                ingest.finish_run(c, run_id, "completed", {})

    def test_refresh_then_reapply(self):
        first = self.apply()
        ex = {k: {row[0] for row in v} for k, v in first["examples"].items()}
        a, b = SETS["A"], SETS["B"]
        self.assertIn(f"{a}|11111-0001|{S2}|C43360", ex["added"])           # site moved in the newer version
        self.assertIn(f"{SET_J}|11111-0009|{S1}|C43360", ex["added"])       # brand-new set
        self.assertIn(f"{a}|11111-0001|{S1}|C43360", ex["removed"])
        self.assertIn(f"{b}|11111-0002|{S2}|C43360", ex["removed"])         # retracted set
        self.assertEqual(first["retractions"]["in_scope"], 2)
        self.assertEqual(first["ingest"]["loaded"], 2)
        self.assertEqual(first["ingest"]["skipped_by_prefix"], 3)           # otc member + 2 change lists
        with db.connect(TEST_DB) as c:
            sel = dict(c.execute("SELECT set_id, selection_status || ':' || selected_version "
                                 "FROM national.set_version_selection").fetchall())
            self.assertEqual(sel[a], "UPDATE_NEWER_VERSION:3")
            self.assertNotIn(b, sel)                                       # withdrawn from the current state ...
            self.assertEqual(c.execute("SELECT count(*) FROM national.spl_document WHERE set_id = %s",
                                       (b,)).fetchone()[0], 1)              # ... but its raw version is kept
            fp = graph.fingerprint(c)
        second = self.apply()
        self.assertEqual(second["changes"], {"added": 0, "removed": 0, "modified": 0, "carried_forward": 0})
        self.assertEqual(second["ingest"]["processed"], 0)
        with db.connect(TEST_DB) as c:
            self.assertEqual(graph.fingerprint(c), fp)
            runs = c.execute("SELECT summary FROM national.refresh_run ORDER BY refresh_id").fetchall()
        self.assertEqual([r[0]["changes"]["added"] > 0 for r in runs], [True, False])


class PureDiff(unittest.TestCase):
    def test_diff_categories(self):
        v = lambda c, ver, fei="1": {"confidence": c, "identity_status": "CURRENT_REGISTERED", "fei": fei,  # noqa: E731
                                     "version": ver}
        d = refresh.diff({"k1": v("DIRECT", 1), "k2": v("DIRECT", 1), "k3": v("DIRECT", 1)},
                         {"k1": v("DIRECT", 2), "k2": v("TENTATIVE", 2), "k4": v("UNKNOWN", 1)}) if db else None
        if d is None:
            self.skipTest("psycopg not installed")
        self.assertEqual({k: [r[0] for r in rows] for k, rows in d.items()},
                         {"added": ["k4"], "removed": ["k3"], "modified": ["k2"], "carried_forward": ["k1"]})


if __name__ == "__main__":
    unittest.main()

"""The published explorer data (site/data/) is intact, internally consistent and free of personal data.

These run without a database. Agreement with the graph itself is checked by
scripts/export_explorer.py --verify and scripts/verify_explorer_csv.py, which need the national database.
"""

import importlib.util
import json
import re
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
DATA = SITE / "data"


def _export_module():
    spec = importlib.util.spec_from_file_location("export_explorer", ROOT / "scripts" / "export_explorer.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _load(rel):
    return json.loads((DATA / rel).read_text(encoding="utf-8"))


class SiteData(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ex = _export_module()
        cls.manifest = _load("manifest.json")

    def test_every_file_matches_its_manifest_checksum(self):
        self.assertEqual(self.ex.check(DATA), [])

    def test_manifest_names_the_committed_export_script(self):
        self.assertEqual(self.manifest["generated_by"]["script_sha256"], self.ex.script_sha256(),
                         "export script changed since the data was generated: re-run scripts/export_explorer.py")

    def test_historical_file_rederives_from_frozen_evidence(self):
        for rel, obj in self.ex.historical_files().items():
            self.assertEqual((DATA / rel).read_bytes(), self.ex.jdump(obj), rel)
        inputs = self.manifest["datasets"]["historical"]["inputs"]
        self.assertEqual(inputs["evidence/historical/frozen/FREEZE_MANIFEST.json"],
                         "361e21bae2bc4fb31e68dfe2f9cf33d03dc8dfb7130c638b1f5012c8596593e3")

    def test_index_counts_equal_exported_edges(self):
        idx = _load("current/facilities.json")
        cols = idx["columns"]
        rows = [dict(zip(cols, r)) for r in idx["rows"]]
        expected = {r["duns"]: (r["mfg_direct"], r["mfg_tentative"], r["mfg_unknown"]) for r in rows}
        got = {}
        for f in sorted((DATA / "current" / "manufacture").glob("*.json")):
            b = json.loads(f.read_text(encoding="utf-8"))
            ec = b["edge_columns"]
            for raw in b["edges"]:
                e = dict(zip(ec, raw))
                self.assertEqual(e["operation"], "MANUFACTURE")
                self.assertEqual(e["duns"][:2], b["shard"])
                self.assertIn(e["set_id"], b["documents"])
                if e["product"] is not None:
                    self.assertIn(str(e["product"]), b["products"])
                c = got.setdefault(e["duns"], [0, 0, 0])
                c[("DIRECT", "TENTATIVE", "UNKNOWN").index(e["confidence"])] += 1
        self.assertEqual({k: tuple(v) for k, v in got.items()}, {k: v for k, v in expected.items() if any(v)})

    def test_examples_hold_all_operations_and_agree_with_index(self):
        idx = _load("current/facilities.json")
        rows = {r[0]: dict(zip(idx["columns"], r)) for r in idx["rows"]}
        for duns in ("093132819", "030606222"):
            b = _load(f"current/examples/{duns}.json")
            ops = {}
            for raw in b["edges"]:
                e = dict(zip(b["edge_columns"], raw))
                ops[e["operation"]] = ops.get(e["operation"], 0) + 1
            r = rows[duns]
            self.assertTrue(r["example"])
            self.assertEqual(ops.pop("MANUFACTURE"), r["mfg_direct"] + r["mfg_tentative"] + r["mfg_unknown"])
            self.assertEqual(ops, r["other_operations"])

    def test_current_and_historical_datasets_stay_separate(self):
        for f in (DATA / "current").rglob("*.json"):
            self.assertEqual(json.loads(f.read_text(encoding="utf-8")).get("dataset"), "current", f)
        self.assertEqual(_load("historical/rocky_mount_2023.json")["dataset"], "historical")
        self.assertEqual(self.manifest["datasets"]["historical"]["cutoff"], "2023-07-18")

    def test_attribution_and_currency_notice_present(self):
        self.assertIn("Courtesy of the U.S. National Library of Medicine", self.manifest["attribution"])
        self.assertIn("do not reflect the most current/accurate data available from NLM", self.manifest["currency"])
        html = (SITE / "index.html").read_text(encoding="utf-8")
        self.assertIn("courtesy of the U.S. National Library of Medicine", html)
        self.assertIn("not affiliated with or endorsed by", html)

    def test_no_personal_data_or_local_paths_in_site(self):
        contact = re.compile(rb"<contactParty|mailto:|tel:\+?[0-9]|[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+\.(?:com|org|net|gov|edu)\b")
        home = re.compile(rb"[A-Za-z]:(?:\\\\|\\|/)+Users(?:\\\\|\\|/)+|/home/[^/\"]+/|/Users/[^/\"]+/")
        hits = [str(p.relative_to(ROOT)) for p in SITE.rglob("*") if p.is_file()
                and (contact.search(p.read_bytes()) or home.search(p.read_bytes()))]
        self.assertEqual(hits, [])

    def test_site_loads_nothing_from_third_parties(self):
        html = (SITE / "index.html").read_text(encoding="utf-8")
        css = (SITE / "style.css").read_text(encoding="utf-8")
        self.assertEqual(re.findall(r'<(?:script|link)\b[^>]*\b(?:src|href)="(?:https?:)?//[^"]*"', html), [])
        self.assertEqual(re.findall(r"@import|url\(\s*['\"]?(?:https?:)?//", css), [])
        for m in re.finditer(r"url\(\s*['\"]?([^'\")]+)", css):
            self.assertTrue((SITE / m.group(1)).is_file(), m.group(1))
        for m in re.finditer(r'<link\b[^>]*\bhref="([^"#:]+)"', html):
            self.assertTrue((SITE / m.group(1)).is_file(), m.group(1))

    def test_self_hosted_fonts_carry_their_licenses(self):
        fonts = sorted((SITE / "fonts").glob("*.woff2"))
        self.assertTrue(fonts)
        for f in fonts:
            family = next(k for k in ("newsreader", "dm-sans", "jetbrains-mono") if f.name.startswith(k))
            text = (SITE / "fonts" / f"LICENSE-{family}.txt").read_text(encoding="utf-8")
            self.assertIn("SIL Open Font License, Version 1.1", text, f.name)
            self.assertEqual(f.read_bytes()[:4], b"wOF2", f.name)
        self.assertIn("SIL Open Font License 1.1", (ROOT / "NOTICE.md").read_text(encoding="utf-8"))

    def test_no_design_study_fixtures_in_site(self):
        # The approved design was a prototype with labelled sample records; production shows only exported data.
        fixture = re.compile(r"design study|sample records?|illustrative|00409-XXXX|SAMPLE_NOT_LOADED|not in sample", re.I)
        hits = [f"{p.name}: {m.group(0)}" for p in SITE.glob("*.*") if p.suffix in (".html", ".js", ".css")
                for m in fixture.finditer(p.read_text(encoding="utf-8"))]
        self.assertEqual(hits, [])

    @unittest.skipUnless(shutil.which("node"), "node not installed")
    def test_frontend_modules_pass_node_syntax_check(self):
        # CI must parse the actual shipped browser modules, not only the Python tests.
        for name in ("app.js", "explorer-core.js"):
            result = subprocess.run(["node", "--check", str(SITE / name)],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, f"{name}: {result.stderr}")

    def test_investigation_story_uses_frozen_historical_export(self):
        # The home story loads the frozen replay, never copies values into JS.
        app = (SITE / "app.js").read_text(encoding="utf-8")
        historical = _load("historical/rocky_mount_2023.json")
        self.assertEqual(historical["metrics"]["E"]["B1_all_hospira_00409"]["N"], 890)
        self.assertEqual(historical["metrics"]["E"]["graph_rocky_mount_direct"]["N"], 480)
        self.assertEqual(historical["metrics"]["E"]["graph_rocky_mount_direct"]["X"], 63)
        self.assertEqual(historical["outcome"]["distinct_package_ndc_11"], 65)
        self.assertIn('load("historical/rocky_mount_2023.json")', app)
        self.assertIn("historical.metrics.E.B1_all_hospira_00409", app)
        self.assertIn("historical.metrics.E.graph_rocky_mount_direct", app)
        self.assertIn("historical.outcome.distinct_package_ndc_11", app)
        self.assertIn("not a shortage forecast", app)
        self.assertIn("snapshot is separate from the 2023 historical test", app)
        self.assertIn("it is not an independently verified production record", app)

    @unittest.skipUnless(shutil.which("node"), "node not installed")
    def test_browser_csv_code_reproduces_exported_rows(self):
        out = json.loads(subprocess.run(["node", str(ROOT / "scripts" / "explorer_csv.mjs"), str(SITE)],
                                        capture_output=True, check=True, encoding="utf-8").stdout)
        rm = out["current"]["093132819"].splitlines()
        self.assertTrue(rm[0].startswith("evidence_id,confidence,reasons,operation,establishment_duns"))
        b = _load("current/examples/093132819.json")
        self.assertEqual(len(rm) - 1, len(b["edges"]))
        hist = out["historical"].splitlines()
        self.assertEqual(len({ln.split(",")[0] for ln in hist[1:]}), 892)  # 890 cohort packages + 2 uncovered


if __name__ == "__main__":
    unittest.main()

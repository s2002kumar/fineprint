"""Integrity checks for the frozen DST-08 review artifacts.

These tests validate the evidence bundle and worksheet shape. They deliberately do
not convert AI review into human adjudication or mark the human gate as passed.
"""
import csv
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DST08 = ROOT / "docs" / "research" / "dst08"
HUMAN_COLUMNS = (
    "human_source_identity_confirmed",
    "human_physical_description_matches_at_relevant_date",
    "human_manufacturing_statement_from_correct_source_and_version",
    "human_verdict",
    "human_reviewer",
    "human_review_date",
    "human_note",
)


def read_csv(name):
    with (DST08 / name).open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def read_json(name):
    with (DST08 / name).open(encoding="utf-8") as stream:
        return json.load(stream)


def source_identity(text):
    match = re.search(r"set\s+([0-9a-f-]{36})\s+v(\d+)", text, re.I)
    return (match.group(1), int(match.group(2))) if match else None


class DST08ReviewArtifactIntegrity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.worksheet = read_csv("final_human_worksheet.csv")
        cls.runbook = (DST08 / "DST_08_HUMAN_REVIEW_RUNBOOK.md").read_text(encoding="utf-8")
        cls.manifest = read_json("sample_manifest.json")
        cls.sample_checks = read_json("sample_checks.json")["results"]
        cls.sample_ai = read_csv("sample_ai_review.csv")
        cls.final_cases = {
            row["case_id"]: row
            for row in read_json("final_cases_evidence.json")["results"]
        }

    def test_worksheet_is_complete_but_does_not_forge_human_signoff(self):
        ids = [row["item_id"] for row in self.worksheet]
        self.assertEqual(len(ids), 52)
        self.assertEqual(len(ids), len(set(ids)))

        expected_counts = {
            "P-R9-": 30,
            "V-": 8,
            "W-": 2,
            "M-": 2,
            "DIRECT-": 10,
        }
        for prefix, expected in expected_counts.items():
            with self.subTest(prefix=prefix):
                self.assertEqual(sum(item.startswith(prefix) for item in ids), expected)

        for row in self.worksheet:
            for column in HUMAN_COLUMNS:
                with self.subTest(item=row["item_id"], column=column):
                    self.assertEqual(row[column].strip(), "")

        # Every frozen item has a concrete source-navigation entry, and the
        # guide explicitly distinguishes AI assistance from human sign-off.
        for item_id in ids:
            with self.subTest(item=item_id):
                self.assertIn(item_id, self.runbook)
        self.assertIn("not a human sign-off", self.runbook.lower())

    def test_random_r9_sample_matches_frozen_manifest_and_rederived_checks(self):
        expected_ids = {f"R9-{number:02d}" for number in range(1, 31)}
        manifest = {row["sample_id"]: row for row in self.manifest["sample"]}
        checks = {row["sample_id"]: row for row in self.sample_checks}
        ai_rows = {row["sample_id"]: row for row in self.sample_ai}
        worksheet_ids = {
            row["item_id"].replace("P-", "")
            for row in self.worksheet
            if row["item_id"].startswith("P-R9-")
        }

        self.assertEqual(worksheet_ids, expected_ids)
        self.assertEqual(set(row_id for row_id in manifest if row_id.startswith("R9-")), expected_ids)
        self.assertEqual(set(row_id for row_id in checks if row_id.startswith("R9-")), expected_ids)
        self.assertEqual(set(row_id for row_id in ai_rows if row_id.startswith("R9-")), expected_ids)

        later_source_count = 0
        for sample_id in sorted(expected_ids):
            with self.subTest(sample_id=sample_id):
                frozen = manifest[sample_id]
                check = checks[sample_id]
                ai = ai_rows[sample_id]

                self.assertEqual(frozen["stratum"], "R9 RESOLVED_DIRECT")
                self.assertEqual(check["mechanical_result"], "ELIGIBLE_SOURCE_LINKED")
                self.assertEqual(check["failed_checks"], [])
                self.assertTrue(all(check["checks"].values()))
                self.assertEqual(check["citing"]["set_id"], frozen["set_id"])
                self.assertEqual(int(check["citing"]["version"]), int(frozen["version"]))
                self.assertEqual(check["citing"]["product_code"], frozen["product_code"])

                candidates = check["candidates"]
                self.assertEqual(len(candidates), 1)
                source = candidates[0]
                self.assertNotEqual(source["set_id"], check["citing"]["set_id"])
                self.assertEqual(source["status"], "DIRECT")
                self.assertTrue(source["form_same"])
                self.assertTrue(source["active_same"])
                self.assertTrue(source["manufacture_performances_scoped_to_code"])
                self.assertTrue(source["direct_edges_all_from_source_xml"])
                self.assertTrue(all(edge["in_source_xml_scoped_to_code"]
                                    for edge in source["graph_manufacture_edges"]))

                source_sites = {
                    duns
                    for performance in source["manufacture_performances_scoped_to_code"]
                    for duns in performance["duns"]
                }
                self.assertTrue(source_sites)
                self.assertEqual(
                    source_sites,
                    set(filter(None, ai["source_direct_sites"].split(";"))),
                )
                self.assertEqual(ai["source_set_id"], source["set_id"])
                self.assertEqual(int(ai["source_version"]), int(source["version"]))
                self.assertEqual(ai["ai_verdict"], "LINK_SUPPORTED")

                published_after = check["temporal"]["source_version_published_after_citing_version"]
                self.assertEqual(ai["source_published_after_citing"].lower(), str(published_after).lower())
                later_source_count += bool(published_after)

        # This is a material caveat in the frozen sample: current-source-label
        # support must not be rewritten as historical or lot-specific site proof.
        self.assertEqual(later_source_count, 17)

    def test_all_eight_version_acceptances_reproduce_site_continuity(self):
        accepted_classes = {
            "VERSION_DRIFT_RESOLVED",
            "NOTATION_ONLY",
            "MULTIPLE_VALID_PRESENTATIONS",
        }
        version_rows = [row for row in self.worksheet if row["item_id"].startswith("V-")]
        self.assertEqual(len(version_rows), 8)

        for row in version_rows:
            with self.subTest(item=row["item_id"]):
                case = self.final_cases[row["item_id"]]
                prototype = case["prototype"]
                reproduced = case["reproduced"]

                self.assertEqual(prototype["v2_status"], "ELIGIBLE")
                self.assertEqual(prototype["v2_basis"], "version_check")
                self.assertIn(prototype["v2_class"], accepted_classes)
                self.assertIsNotNone(prototype["v2_applicable_version"])
                self.assertTrue(prototype["v2_continuing_sites"])
                self.assertTrue(reproduced["source_set_reproduced"])
                self.assertTrue(reproduced["physical_now_reproduced"])
                self.assertTrue(reproduced["v2_class_reproduced"])
                self.assertTrue(reproduced["v2_applicable_version_reproduced"])
                self.assertTrue(reproduced["v2_continuing_sites_reproduced"])

                citing = source_identity(row["citing"])
                source = source_identity(row["source"])
                applicable = source_identity(row["relevant_version"])
                self.assertIsNotNone(citing)
                self.assertIsNotNone(source)
                self.assertIsNotNone(applicable)
                self.assertEqual(citing, (case["citing"]["set_id"], int(case["citing"]["version"])))
                self.assertEqual(source, (case["source"]["set_id"], int(case["source"]["version"])))
                self.assertEqual(applicable[1], int(prototype["v2_applicable_version"]))


if __name__ == "__main__":
    unittest.main()

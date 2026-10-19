"""Archive safety, nested-ZIP processing, tallies, NDC rules and release-page parsing."""

import io
import unittest
import warnings
import zipfile

from fineprint import bulk, dailymed, ndc, safezip
from tests import HIST

FIXTURE = "5558a5f5-e821-473b-7d8a-5d33d09f0586_v19.xml"
MEMBER = "prescription/20200901_5558a5f5-e821-473b-7d8a-5d33d09f0586.zip"


def make_zip(entries, compression=zipfile.ZIP_DEFLATED):
    buf = io.BytesIO()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")  # duplicate-name warning is the point of one test
        with zipfile.ZipFile(buf, "w", compression) as z:
            for name, data in entries:
                z.writestr(name, data)
    return buf.getvalue()


class Names(unittest.TestCase):
    def test_unsafe_names(self):
        self.assertIn("parent_traversal", safezip.name_problems("prescription/../../evil.zip"))
        self.assertIn("absolute_path", safezip.name_problems("/etc/passwd"))
        self.assertIn("absolute_path", safezip.name_problems("C:/x.zip"))
        self.assertIn("backslash_in_name", safezip.name_problems("a\\b.zip"))
        self.assertEqual(safezip.name_problems(MEMBER), [])


class Limits(unittest.TestCase):
    def test_bounded_reader_stops(self):
        with self.assertRaises(safezip.ZipSafetyError):
            safezip.BoundedReader(io.BytesIO(b"x" * 2000), 1000).read()

    def test_read_member_cap(self):
        z = zipfile.ZipFile(io.BytesIO(make_zip([("a.xml", b"x" * 5000)])))
        with self.assertRaises(safezip.ZipSafetyError):
            safezip.read_member(z, z.getinfo("a.xml"), 1000)

    def test_compression_bomb_flagged(self):
        z = zipfile.ZipFile(io.BytesIO(make_zip([("big.xml", b"\0" * (12 << 20))])))
        self.assertIn("suspicious_compression_ratio", safezip.member_problems(z.getinfo("big.xml")))

    def test_duplicate_names_detected(self):
        z = zipfile.ZipFile(io.BytesIO(make_zip([("a.zip", b"1"), ("a.zip", b"2")])))
        self.assertEqual(safezip.scan_directory(z)["duplicate_names"], ["a.zip"])


class NestedProcessing(unittest.TestCase):
    def setUp(self):
        self.xml = (HIST / FIXTURE).read_bytes()

    def test_real_fixture_ok(self):
        r = bulk.process_nested_zip(MEMBER, make_zip([("x.xml", self.xml), ("a.jpg", b"\xff\xd8")]))
        self.assertEqual(r["status"], "ok")
        self.assertEqual(r["products_with_manufacture_duns"], ["0409-3307", "0409-3308"])
        self.assertIn("093132819", r["manufacture_duns"])
        self.assertNotIn("141588017", r["establishment_duns"])  # labeler is not a facility

    def test_corrupt_nested_zip(self):
        r = bulk.process_nested_zip(MEMBER, b"PK\x03\x04garbage")
        self.assertEqual(r["status"], "failed")
        self.assertTrue(r["failure"].startswith("bad_nested_zip"))

    def test_missing_and_duplicate_xml(self):
        self.assertEqual(bulk.process_nested_zip(MEMBER, make_zip([("a.jpg", b"1")]))["failure"], "xml_member_count_0")
        two = make_zip([("a.xml", self.xml), ("b.xml", self.xml)])
        self.assertEqual(bulk.process_nested_zip(MEMBER, two)["failure"], "xml_member_count_2")

    def test_malformed_xml(self):
        r = bulk.process_nested_zip(MEMBER, make_zip([("a.xml", self.xml[:5000])]))
        self.assertTrue(r["failure"].startswith("xml_parse_error"))

    def test_traversal_member_inside_nested_zip(self):
        r = bulk.process_nested_zip(MEMBER, make_zip([("../a.xml", self.xml)]))
        self.assertTrue(r["failure"].startswith("unsafe_xml_member"))

    def test_duplicate_documents_counted(self):
        t = bulk.Tally()
        data = make_zip([("x.xml", self.xml)])
        t.add(bulk.process_nested_zip(MEMBER, data))
        t.add(bulk.process_nested_zip(MEMBER, data))
        d = t.to_dict()
        self.assertEqual(d["distinct_set_ids"], 1)
        self.assertEqual(d["set_ids_seen_more_than_once"], 1)


class Ndc(unittest.TestCase):
    def test_11_digit_only_from_explicit_segments(self):
        self.assertEqual(ndc.to_11_digit("0409-3308-03"), "00409-3308-03")
        self.assertEqual(ndc.to_11_digit("12345-678-90"), "12345-0678-90")
        self.assertEqual(ndc.to_11_digit("12345-6789-0"), "12345-6789-00")
        self.assertIsNone(ndc.to_11_digit("0409330803"))
        self.assertIsNone(ndc.to_11_digit("0409-3308"))

    def test_package_product_relationship_is_raw(self):
        self.assertTrue(ndc.package_belongs_to_product("0409-3308-03", "0409-3308"))
        self.assertFalse(ndc.package_belongs_to_product("0409-3308-03", "00409-3308"))
        self.assertFalse(ndc.package_belongs_to_product("0409-3308-03", "0409-3307"))


class ReleasePage(unittest.TestCase):
    HTML = ('<a href="https://dailymed-data.nlm.nih.gov/public-release-files/dm_spl_release_human_rx_part1.zip">x</a>'
            '<li>dm_spl_release_human_rx_part1.zip [ HTTPS / FTP ] Number of files: 14,989 File size: 3.00GB '
            'MD5 checksum: 1db0117254ddc9d8da8d142dc155e374 Last Modified: Oct 16, 2026</li>')

    def test_parse_parts(self):
        (p,) = dailymed.parse_release_parts(self.HTML)
        self.assertEqual(p["advertised_number_of_files"], 14989)
        self.assertEqual(p["advertised_md5"], "1db0117254ddc9d8da8d142dc155e374")
        self.assertEqual(p["advertised_last_modified"], "2026-10-16")
        self.assertTrue(p["https_url"].endswith("part1.zip"))

    def test_later_version_excluded_by_cutoff(self):
        # Aminophylline history: v27 published 2023-08-28 must never be chosen for 2023-07-18.
        versions = [{"version": 25, "published_at": "2019-11-26"}, {"version": 26, "published_at": "2022-12-02"},
                    {"version": 27, "published_at": "2023-08-28"}]
        self.assertEqual(dailymed.latest_admissible(versions, "2023-07-18")["version"], 26)
        self.assertIsNone(dailymed.latest_admissible(versions, "2010-01-01"))


if __name__ == "__main__":
    unittest.main()

"""Golden checks on real archived (pre-2023-07-18) SPL versions fetched in DST-00."""

import unittest
import xml.etree.ElementTree as ET

from fineprint import spl
from tests import HIST

ROCKY_MOUNT = "093132819"
MCPHERSON = "030606222"
HOSPIRA_LABELER = "141588017"
LAKE_FOREST_HQ = "827731089"


def parse(name):
    with open(HIST / name, "rb") as fh:
        return spl.parse_spl(fh)


def mfg(doc, duns):
    return sorted({e["product_code"] for e in spl.operation_edges(doc)
                   if e["duns"] == duns and e["operation_code"] == spl.MANUFACTURE_CODE})


def resolve_loc(xml_path, loc):
    """Evaluate a parser ``loc`` against the raw XML with ElementTree positional paths."""
    root = ET.parse(xml_path).getroot()
    steps = loc.strip("/").split("/")[1:]  # drop leading 'document'
    path = "./" + "/".join("{urn:hl7-org:v3}" + s for s in steps)
    return root.find(path)


class FiveRockyMountTargets(unittest.TestCase):
    EXPECTED = {
        "5558a5f5-e821-473b-7d8a-5d33d09f0586_v19.xml": ["0409-3307", "0409-3308"],
        "1c5bc1dd-e9ec-44c1-9281-67ad482315d9_v17.xml": ["0409-4346"],
        "9a663ef3-881f-48bd-2689-3713b24545c2_v26.xml": ["0409-5921", "0409-5922"],
        "ad8916e7-206e-409e-2582-30d072845dd4_v25.xml": ["0409-1630", "0409-4910", "0409-4911", "0409-9630"],
        "c4c65e48-85f8-4dcf-6281-06e40959cc79_v18.xml": ["0409-1631", "0409-4928"],
    }

    def test_manufacture_at_rocky_mount(self):
        for name, codes in self.EXPECTED.items():
            with self.subTest(name=name):
                doc = parse(name)
                set_id, v = name[:-4].split("_v")
                self.assertEqual(doc["set_id"], set_id)
                self.assertEqual(doc["version"], v)
                self.assertEqual(mfg(doc, ROCKY_MOUNT), codes)
                self.assertEqual(mfg(doc, MCPHERSON), [])

    def test_every_manufacture_citation_resolves_in_raw_xml(self):
        for name in self.EXPECTED:
            doc = parse(name)
            for e in spl.operation_edges(doc):
                if e["operation_code"] != spl.MANUFACTURE_CODE:
                    continue
                perf = resolve_loc(HIST / name, e["loc"])
                self.assertIsNotNone(perf, e["loc"])
                code = perf.find("{urn:hl7-org:v3}actDefinition/{urn:hl7-org:v3}code")
                self.assertEqual(code.get("code"), "C43360")
                kinds = [c.get("code") for c in perf.iter("{urn:hl7-org:v3}manufacturedMaterialKind")
                         for c in c.findall("{urn:hl7-org:v3}code")]
                self.assertIn(e["product_code"], kinds)


class OperationSemantics(unittest.TestCase):
    def test_labeler_is_not_an_establishment(self):
        doc = parse("5558a5f5-e821-473b-7d8a-5d33d09f0586_v19.xml")
        self.assertEqual([o["duns"] for o in spl.labelers(doc)], [[HOSPIRA_LABELER]])
        self.assertNotIn(HOSPIRA_LABELER, {e["duns"] for e in spl.operation_edges(doc)})

    def test_pack_and_label_never_become_manufacture(self):
        doc = parse("5558a5f5-e821-473b-7d8a-5d33d09f0586_v19.xml")
        edges = spl.operation_edges(doc)
        for e in edges:
            if e["operation"].strip().upper() in {"PACK", "LABEL", "ANALYSIS"}:
                self.assertNotEqual(e["operation_code"], spl.MANUFACTURE_CODE)
        self.assertTrue(any(e["operation"] == "PACK" for e in edges))

    def test_analysis_only_hq_duns_has_no_manufacture(self):
        doc = parse("5558a5f5-e821-473b-7d8a-5d33d09f0586_v19.xml")
        ops = {e["operation"] for e in spl.operation_edges(doc) if e["duns"] == LAKE_FOREST_HQ}
        self.assertEqual(ops, {"ANALYSIS"})

    def test_api_manufacture_is_a_distinct_operation(self):
        doc = parse("ad8916e7-206e-409e-2582-30d072845dd4_v25.xml")
        rolabo = [e for e in spl.operation_edges(doc) if e["duns"] == "513603225"]
        self.assertTrue(rolabo)
        self.assertTrue(all(e["operation_code"] == "C82401" for e in rolabo))
        self.assertEqual(mfg(doc, "513603225"), [])

    def test_multiple_facilities_per_product(self):
        doc = parse("ad8916e7-206e-409e-2582-30d072845dd4_v25.xml")
        duns = {e["duns"] for e in spl.operation_edges(doc) if e["product_code"] == "0409-1630"}
        self.assertEqual(duns, {ROCKY_MOUNT, LAKE_FOREST_HQ, "513603225", "831351445"})


class McPhersonControls(unittest.TestCase):
    def test_mcpherson_manufactured_products(self):
        self.assertEqual(mfg(parse("b598c237-032d-4bb5-0e92-50eabd863dac_v23.xml"), MCPHERSON), ["0409-1782"])
        self.assertEqual(mfg(parse("41044928-dd1f-40bf-1fa6-709dff559124_v17.xml"), MCPHERSON), ["0409-1273"])
        self.assertEqual(mfg(parse("b598c237-032d-4bb5-0e92-50eabd863dac_v23.xml"), ROCKY_MOUNT), [])

    def test_same_drug_name_different_site(self):
        # Diazepam 7e7dd743 v24: made at Rocky Mount; McPherson only ANALYSIS.
        doc = parse("7e7dd743-a87b-4ab3-b6ae-f116cd0c8b0f_v24.xml")
        self.assertEqual(mfg(doc, ROCKY_MOUNT), ["0409-3213"])
        self.assertEqual({e["operation"] for e in spl.operation_edges(doc) if e["duns"] == MCPHERSON}, {"ANALYSIS"})


class Packages(unittest.TestCase):
    def test_nested_package_hierarchy(self):
        doc = parse("5558a5f5-e821-473b-7d8a-5d33d09f0586_v19.xml")
        p = next(p for p in doc["products"] if p["product_ndc_raw"] == "0409-3307")
        pk = {k["package_ndc_raw"]: k for k in p["packages"]}
        self.assertEqual(pk["0409-3307-11"]["contains"], "0409-3307")
        self.assertEqual(pk["0409-3307-11"]["form"], "VIAL")
        self.assertEqual(pk["0409-3307-03"]["contains"], "0409-3307-11")
        self.assertEqual(pk["0409-3307-03"]["level"], 2)

    def test_package_without_ndc_is_kept_as_none(self):
        doc = parse("c4c65e48-85f8-4dcf-6281-06e40959cc79_v18.xml")
        p = next(p for p in doc["products"] if p["product_ndc_raw"] == "0409-4928")
        self.assertIn(None, [k["package_ndc_raw"] for k in p["packages"]])


class IdentityFiling(unittest.TestCase):
    def test_rocky_mount_duns_fei_address(self):
        doc = parse("f435e79d-dea3-49dc-8268-146c60ba52a1_v7.contacts-removed.xml")
        rm = [o for o in spl.establishments(doc) if ROCKY_MOUNT in o["duns"]]
        self.assertEqual(len(rm), 1)
        self.assertEqual(rm[0]["fei"], ["1021343"])
        self.assertEqual(rm[0]["address"]["street"], ["Highway 301 North"])
        self.assertEqual((rm[0]["address"]["city"], rm[0]["address"]["state"]), ("Rocky Mount", "NC"))
        self.assertEqual(doc["effective_time"], "20150515")


if __name__ == "__main__":
    unittest.main()

"""Synthetic edge cases: malformed, unsafe, legacy and missing-data SPL documents."""

import io
import unittest
import xml.etree.ElementTree as ET

from fineprint import spl

HEAD = '<?xml version="1.0" encoding="UTF-8"?>\n<document xmlns="urn:hl7-org:v3">'


def doc_xml(author="", body="", version="3"):
    return (f'{HEAD}<id root="d1"/><code code="34391-3" displayName="HUMAN PRESCRIPTION DRUG LABEL"/>'
            f'<effectiveTime value="20230101"/><setId root="s1"/><versionNumber value="{version}"/>'
            f'<author><assignedEntity>{author}</assignedEntity></author>'
            f'<component><structuredBody>{body}</structuredBody></component></document>').encode()


def est(duns_xml, ops):
    perf = "".join(
        f'<performance><actDefinition><code code="{c}" displayName="{n}"/>'
        + "".join(f'<product><manufacturedProduct><manufacturedMaterialKind><code code="{p}"/>'
                  f'</manufacturedMaterialKind></manufacturedProduct></product>' for p in prods)
        + '</actDefinition></performance>' for c, n, prods in ops)
    return (f'<representedOrganization><id root="{spl.DUNS_ROOT}" extension="111111111"/><name>Labeler</name>'
            f'<assignedEntity><assignedOrganization><assignedEntity><assignedOrganization>{duns_xml}<name>Site</name>'
            f'</assignedOrganization>{perf}</assignedEntity></assignedOrganization></assignedEntity>'
            f'</representedOrganization>')


def parse(b, **kw):
    return spl.parse_spl(io.BytesIO(b), **kw)


class Unsafe(unittest.TestCase):
    def test_entity_expansion_rejected(self):
        bomb = (b'<?xml version="1.0"?><!DOCTYPE d [<!ENTITY a "aaaaaaaaaa"><!ENTITY b "&a;&a;&a;&a;">]>'
                b'<document xmlns="urn:hl7-org:v3">&b;</document>')
        with self.assertRaises(spl.SplRejected):
            parse(bomb)

    def test_late_dtd_after_prologue_scan_is_rejected(self):
        # Valid XML with a DOCTYPE after 64 KiB of legal prologue whitespace.
        # The old fixed-size first-chunk scan accepted and expanded its entity.
        prefix = b'<?xml version="1.0"?>' + b' ' * (spl.PROLOGUE_SCAN_BYTES + 64)
        xml = prefix + (b'<!DOCTYPE document [<!ENTITY demo "EXPANDED">]>'
                        b'<document xmlns="urn:hl7-org:v3"><title>&demo;</title></document>')
        with self.assertRaises(spl.SplRejected):
            parse(xml)

    def test_dtd_marker_split_across_initial_read_is_rejected(self):
        prefix = b'<?xml version="1.0"?>'
        xml = (prefix + b' ' * (spl.PROLOGUE_SCAN_BYTES - len(prefix) - 4)
               + b'<!DOCTYPE document [<!ENTITY demo "x">]>'
               + b'<document xmlns="urn:hl7-org:v3"/>')
        with self.assertRaises(spl.SplRejected):
            parse(xml)

    def test_wrong_root_rejected(self):
        with self.assertRaises(spl.SplRejected):
            parse(b'<?xml version="1.0"?><notspl xmlns="urn:hl7-org:v3"/>')

    def test_truncated_xml_raises_parse_error(self):
        b = doc_xml()
        with self.assertRaises(ET.ParseError):
            parse(b[: len(b) // 2])

    def test_size_cap(self):
        with self.assertRaises(spl.SplRejected):
            parse(doc_xml(body="<component>" + "x" * 5000 + "</component>"), max_bytes=1000)


class MissingData(unittest.TestCase):
    def test_establishment_without_duns_is_unknown_identity(self):
        d = parse(doc_xml(author=est("", [("C43360", "MANUFACTURE", ["1234-5678"])])))
        edges = spl.operation_edges(d)
        self.assertEqual(len(edges), 1)
        self.assertIsNone(edges[0]["duns"])

    def test_operation_without_product_scope(self):
        d = parse(doc_xml(author=est(f'<id root="{spl.DUNS_ROOT}" extension="222222222"/>',
                                     [("C73606", "REPACK", [])])))
        self.assertIsNone(spl.operation_edges(d)[0]["product_code"])

    def test_no_establishments_yields_no_edges(self):
        d = parse(doc_xml(author='<representedOrganization><id root="x" extension="1"/><name>L</name>'
                                 '</representedOrganization>'))
        self.assertEqual(spl.establishments(d), [])
        self.assertEqual(spl.operation_edges(d), [])

    def test_display_name_case_does_not_change_operation_code(self):
        d = parse(doc_xml(author=est(f'<id root="{spl.DUNS_ROOT}" extension="333333333"/>',
                                     [("C43360", "manufacture ", ["1234-5678"])])))
        e = spl.operation_edges(d)[0]
        self.assertEqual(e["operation_code"], spl.MANUFACTURE_CODE)
        self.assertEqual(e["operation"], "manufacture ")  # raw value preserved

    def test_performance_outside_author_flagged(self):
        body = ('<component><section><code code="48780-1"/><performance><actDefinition><code code="C43360"/>'
                '</actDefinition></performance></section></component>')
        d = parse(doc_xml(body=body))
        self.assertIn("performance_outside_author", [a["kind"] for a in d["anomalies"]])


class Legacy(unittest.TestCase):
    def test_r4_manufactured_medicine_and_packaged_medicine(self):
        body = ('<component><section><code code="48780-1"/><subject><manufacturedProduct>'
                '<manufacturedMedicine><code code="0409-1111"/><name>Old</name>'
                '<asContent><containerPackagedMedicine><code code="0409-1111-01"/></containerPackagedMedicine>'
                '</asContent></manufacturedMedicine></manufacturedProduct></subject></section></component>')
        d = parse(doc_xml(body=body))
        self.assertEqual(d["products"][0]["product_ndc_raw"], "0409-1111")
        self.assertEqual(d["products"][0]["packages"][0]["package_ndc_raw"], "0409-1111-01")

    def test_versions_reported_verbatim(self):
        self.assertEqual(parse(doc_xml(version="19"))["version"], "19")


if __name__ == "__main__":
    unittest.main()
